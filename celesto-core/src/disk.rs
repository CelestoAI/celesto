//! Native disk/image helpers for sparse VM images.

use std::ffi::CString;
use std::fs::{self, File};
use std::io::{self, Read, Seek, SeekFrom, Write};
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

const SPARSE_CHUNK_SIZE: usize = 1024 * 1024;

/// Copy a VM image using reflink when available, preserving sparse holes otherwise.
pub fn clone_or_sparse_copy(source: &str, target: &str) -> io::Result<String> {
    let mut source = File::open(source)?;
    let metadata = source.metadata()?;
    if !metadata.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "source is not a regular file",
        ));
    }
    let mut stage = StagedOutput::new(Path::new(target))?;
    let method = if reflink_copy(&source, &stage.file).is_ok() {
        "reflink"
    } else {
        // A failed clone may leave partial output. Reuse the same descriptor.
        stage.file.set_len(0)?;
        stage.file.seek(SeekFrom::Start(0))?;
        let mut buffer = vec![0_u8; SPARSE_CHUNK_SIZE];
        loop {
            let read = source.read(&mut buffer)?;
            if read == 0 {
                break;
            }
            write_sparse_chunk(&mut stage.file, &buffer[..read])?;
        }
        stage.file.set_len(metadata.len())?;
        "sparse"
    };
    stage.file.set_permissions(metadata.permissions())?;
    stage.finish()?;
    Ok(method.to_string())
}

/// Identify a caller's decompression budget separately from corrupt input or I/O failure.
#[derive(Debug, thiserror::Error)]
#[error("decoded image exceeds size limit")]
pub(crate) struct ImageSizeLimitError;

/// Decompress a trusted image without a size budget. Imports should use the bounded API.
pub fn decompress_zstd_sparse(source: &str, target: &str, chunk_size: usize) -> io::Result<String> {
    decompress_zstd_sparse_bounded(source, target, chunk_size, None)
}

/// Reject decoded output exceeding the supplied budget before writing it.
pub fn decompress_zstd_sparse_bounded(
    source: &str,
    target: &str,
    chunk_size: usize,
    max_output_bytes: Option<u64>,
) -> io::Result<String> {
    if chunk_size == 0 {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "chunk_size must be greater than zero",
        ));
    }
    let mut decoder = zstd::stream::read::Decoder::new(File::open(source)?)?;
    let mut stage = StagedOutput::new(Path::new(target))?;
    let mut size = 0_u64;
    // A caller-provided chunk size must not cause an unbounded allocation either.
    let mut buffer = vec![0_u8; chunk_size.min(SPARSE_CHUNK_SIZE)];
    loop {
        let read = decoder.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        size = size
            .checked_add(read as u64)
            .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, ImageSizeLimitError))?;
        if max_output_bytes.is_some_and(|limit| size > limit) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                ImageSizeLimitError,
            ));
        }
        write_sparse_chunk(&mut stage.file, &buffer[..read])?;
    }
    stage.file.set_len(size)?;
    stage.finish()?;
    Ok("sparse".to_string())
}

/// Retain both directory descriptors and the exclusive output file until rename.
/// The private directory prevents other accounts with access to the destination
/// directory from replacing the stage entry or reading incomplete image bytes.
struct StagedOutput {
    parent: File,
    directory: File,
    directory_name: CString,
    target_name: CString,
    file: File,
}

impl StagedOutput {
    fn new(target: &Path) -> io::Result<Self> {
        let target_name = c_name(
            target
                .file_name()
                .ok_or_else(|| {
                    io::Error::new(io::ErrorKind::InvalidInput, "target path has no filename")
                })?
                .as_bytes(),
        )?;
        let parent_path = target
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        fs::create_dir_all(parent_path)?;
        let parent = File::open(parent_path)?;
        for attempt in 0..100 {
            let name = c_name(
                format!(
                    ".celesto-disk-{}-{}-{attempt}",
                    std::process::id(),
                    SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap_or_default()
                        .as_nanos()
                )
                .as_bytes(),
            )?;
            let rc = unsafe { libc::mkdirat(parent.as_raw_fd(), name.as_ptr(), 0o700) };
            if rc != 0 {
                let error = io::Error::last_os_error();
                if error.kind() == io::ErrorKind::AlreadyExists {
                    continue;
                }
                return Err(error);
            }
            let result = (|| {
                let directory = open_at(
                    &parent,
                    &name,
                    libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW,
                    0,
                )?;
                let metadata = directory.metadata()?;
                if metadata.uid() != unsafe { libc::geteuid() } || metadata.mode() & 0o077 != 0 {
                    return Err(io::Error::new(
                        io::ErrorKind::PermissionDenied,
                        "image staging directory is not private",
                    ));
                }
                let file = open_at(
                    &directory,
                    c"data",
                    libc::O_WRONLY | libc::O_CREAT | libc::O_EXCL | libc::O_NOFOLLOW,
                    0o600,
                )?;
                Ok((directory, file))
            })();
            match result {
                Ok((directory, file)) => {
                    return Ok(Self {
                        parent,
                        directory,
                        directory_name: name,
                        target_name,
                        file,
                    });
                }
                Err(error) => {
                    unsafe {
                        libc::unlinkat(parent.as_raw_fd(), name.as_ptr(), libc::AT_REMOVEDIR);
                    }
                    return Err(error);
                }
            }
        }
        Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            "cannot create image staging directory",
        ))
    }

    fn finish(&self) -> io::Result<()> {
        self.file.sync_all()?;
        let rc = unsafe {
            libc::renameat(
                self.directory.as_raw_fd(),
                c"data".as_ptr(),
                self.parent.as_raw_fd(),
                self.target_name.as_ptr(),
            )
        };
        if rc != 0 {
            return Err(io::Error::last_os_error());
        }
        self.parent.sync_all()
    }
}

impl Drop for StagedOutput {
    fn drop(&mut self) {
        unsafe {
            libc::unlinkat(self.directory.as_raw_fd(), c"data".as_ptr(), 0);
            libc::unlinkat(
                self.parent.as_raw_fd(),
                self.directory_name.as_ptr(),
                libc::AT_REMOVEDIR,
            );
        }
    }
}

fn c_name(name: &[u8]) -> io::Result<CString> {
    CString::new(name)
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, "path contains a zero byte"))
}

fn open_at(
    parent: &File,
    name: &std::ffi::CStr,
    flags: i32,
    mode: libc::mode_t,
) -> io::Result<File> {
    let fd = unsafe {
        libc::openat(
            parent.as_raw_fd(),
            name.as_ptr(),
            flags | libc::O_CLOEXEC,
            mode as libc::c_uint,
        )
    };
    if fd < 0 {
        Err(io::Error::last_os_error())
    } else {
        Ok(unsafe { File::from_raw_fd(fd) })
    }
}

#[cfg(target_os = "linux")]
fn reflink_copy(source: &File, target: &File) -> io::Result<()> {
    let rc = unsafe { libc::ioctl(target.as_raw_fd(), libc::FICLONE, source.as_raw_fd()) };
    if rc == 0 {
        Ok(())
    } else {
        Err(io::Error::last_os_error())
    }
}

#[cfg(not(target_os = "linux"))]
fn reflink_copy(_source: &File, _target: &File) -> io::Result<()> {
    Err(io::Error::new(
        io::ErrorKind::Unsupported,
        "reflink copy is not available on this platform",
    ))
}

fn write_sparse_chunk(target: &mut File, chunk: &[u8]) -> io::Result<()> {
    if chunk.iter().all(|byte| *byte == 0) {
        target.seek(SeekFrom::Current(chunk.len() as i64))?;
    } else {
        target.write_all(chunk)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bounded_decode_rejects_before_replacing_target_and_removes_stage() {
        let dir = std::env::temp_dir().join(format!(
            "celesto-disk-limit-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&dir).unwrap();
        let source = dir.join("image.zst");
        let target = dir.join("image");
        fs::write(
            &source,
            zstd::stream::encode_all(&b"123456789"[..], 1).unwrap(),
        )
        .unwrap();
        fs::write(&target, b"old image").unwrap();
        let error = decompress_zstd_sparse_bounded(
            source.to_str().unwrap(),
            target.to_str().unwrap(),
            4,
            Some(8),
        )
        .unwrap_err();
        assert!(error.to_string().contains("limit"));
        assert_eq!(fs::read(&target).unwrap(), b"old image");
        assert_eq!(fs::read_dir(&dir).unwrap().count(), 2);
        decompress_zstd_sparse_bounded(
            source.to_str().unwrap(),
            target.to_str().unwrap(),
            4,
            Some(9),
        )
        .unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"123456789");
        let copy = dir.join("copy");
        clone_or_sparse_copy(target.to_str().unwrap(), copy.to_str().unwrap()).unwrap();
        assert_eq!(fs::read(&copy).unwrap(), b"123456789");
        fs::remove_dir_all(dir).unwrap();
    }

    #[test]
    fn decompress_ignores_attacker_owned_sibling_stage() {
        let dir = std::env::temp_dir().join(format!(
            "celesto-disk-security-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&dir).unwrap();
        let source = dir.join("image.zst");
        let target = dir.join("image");
        let victim = dir.join("victim");
        fs::write(
            &source,
            zstd::stream::encode_all(&b"decoded image"[..], 1).unwrap(),
        )
        .unwrap();
        fs::write(&victim, b"private existing contents").unwrap();
        std::os::unix::fs::symlink(&victim, dir.join("image.tmp")).unwrap();
        decompress_zstd_sparse(source.to_str().unwrap(), target.to_str().unwrap(), 4).unwrap();
        let victim_bytes = fs::read(&victim).unwrap();
        assert_eq!(fs::read(target).unwrap(), b"decoded image");
        fs::remove_dir_all(dir).unwrap();
        assert_eq!(victim_bytes, b"private existing contents");
    }
}
