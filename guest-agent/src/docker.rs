//! Optional Docker daemon supervisor for sandboxes without systemd.
//!
//! Celesto keeps a custom `/init` (no systemd). When a user installs
//! `docker.io`, nothing starts `dockerd` automatically. This module polls for
//! an executable `dockerd`, starts it if `/run/docker.sock` is not healthy, and
//! restarts it with backoff on crash. A `SIGUSR1` on the guest agent wakes the
//! discovery loop early (optional apt hooks can send that signal).

use std::fs::{self, OpenOptions};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::time::Duration;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::UnixStream;
use tokio::process::{Child, Command};
use tokio::sync::watch;
use tokio::time::{Instant, MissedTickBehavior};

const DOCKER_SOCKET: &str = "/run/docker.sock";
const DOCKER_LOG: &str = "/var/log/celesto-docker.log";
const STARTUP_TIMEOUT: Duration = Duration::from_secs(30);
const HEALTH_INTERVAL: Duration = Duration::from_secs(10);
const DISCOVERY_INTERVAL: Duration = Duration::from_secs(2);
const RESTART_DELAYS: [Duration; 5] = [
    Duration::from_secs(1),
    Duration::from_secs(2),
    Duration::from_secs(5),
    Duration::from_secs(10),
    Duration::from_secs(30),
];

const DOCKERD_CANDIDATES: [&str; 3] = [
    "/usr/bin/dockerd",
    "/usr/local/bin/dockerd",
    "/usr/sbin/dockerd",
];

pub async fn run(mut rescan: watch::Receiver<u64>) {
    let mut failures = 0usize;

    loop {
        let Some(dockerd) = discover_dockerd(&DOCKERD_CANDIDATES) else {
            tokio::select! {
                changed = rescan.changed() => {
                    if changed.is_err() {
                        return;
                    }
                }
                _ = tokio::time::sleep(DISCOVERY_INTERVAL) => {}
            }
            continue;
        };

        if docker_ready(Path::new(DOCKER_SOCKET)).await {
            tracing::info!(path = %dockerd.display(), "docker daemon is already running");
            monitor_adopted_daemon(&mut rescan).await;
            continue;
        }

        tracing::info!(path = %dockerd.display(), "starting docker daemon");
        match spawn_dockerd(&dockerd) {
            Ok(mut child) => match wait_until_ready(&mut child).await {
                StartResult::Ready => {
                    failures = 0;
                    tracing::info!(path = %dockerd.display(), "docker daemon is ready");
                    let status = child.wait().await;
                    tracing::warn!(?status, "docker daemon exited");
                }
                StartResult::Exited(status) => {
                    tracing::warn!(?status, "docker daemon exited before becoming ready");
                }
                StartResult::TimedOut => {
                    tracing::warn!("docker daemon did not become ready within 30 seconds");
                    terminate_child(&mut child).await;
                }
            },
            Err(error) => {
                tracing::warn!(%error, path = %dockerd.display(), "failed to start docker daemon");
            }
        }

        let delay = restart_delay(failures);
        failures = failures.saturating_add(1);
        tracing::info!(delay_seconds = delay.as_secs(), "docker restart scheduled");
        tokio::select! {
            changed = rescan.changed() => {
                if changed.is_err() {
                    return;
                }
            }
            _ = tokio::time::sleep(delay) => {}
        }
    }
}

fn discover_dockerd(candidates: &[&str]) -> Option<PathBuf> {
    candidates.iter().map(PathBuf::from).find(|path| {
        fs::metadata(path)
            .map(|metadata| metadata.is_file() && metadata.permissions().mode() & 0o111 != 0)
            .unwrap_or(false)
    })
}

fn spawn_dockerd(path: &Path) -> std::io::Result<Child> {
    let stdout = OpenOptions::new()
        .create(true)
        .append(true)
        .open(DOCKER_LOG)?;
    let stderr = stdout.try_clone()?;

    Command::new(path)
        .current_dir("/")
        .env(
            "PATH",
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        )
        .env("HOME", "/root")
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr))
        .spawn()
}

enum StartResult {
    Ready,
    Exited(std::io::Result<std::process::ExitStatus>),
    TimedOut,
}

async fn wait_until_ready(child: &mut Child) -> StartResult {
    let deadline = Instant::now() + STARTUP_TIMEOUT;
    let mut interval = tokio::time::interval(Duration::from_millis(200));
    interval.set_missed_tick_behavior(MissedTickBehavior::Delay);

    loop {
        tokio::select! {
            status = child.wait() => return StartResult::Exited(status),
            _ = interval.tick() => {
                if docker_ready(Path::new(DOCKER_SOCKET)).await {
                    return StartResult::Ready;
                }
                if Instant::now() >= deadline {
                    return StartResult::TimedOut;
                }
            }
        }
    }
}

async fn monitor_adopted_daemon(rescan: &mut watch::Receiver<u64>) {
    let mut failures = 0u8;
    let mut interval = tokio::time::interval(HEALTH_INTERVAL);
    interval.set_missed_tick_behavior(MissedTickBehavior::Delay);

    loop {
        tokio::select! {
            changed = rescan.changed() => {
                if changed.is_err() {
                    return;
                }
            }
            _ = interval.tick() => {
                if docker_ready(Path::new(DOCKER_SOCKET)).await {
                    failures = 0;
                } else {
                    failures += 1;
                    if failures >= 3 {
                        tracing::warn!("adopted docker daemon is unhealthy");
                        return;
                    }
                }
            }
        }
    }
}

async fn docker_ready(socket: &Path) -> bool {
    let Ok(Ok(mut stream)) =
        tokio::time::timeout(Duration::from_secs(1), UnixStream::connect(socket)).await
    else {
        return false;
    };

    if stream
        .write_all(b"GET /_ping HTTP/1.0\r\nHost: docker\r\n\r\n")
        .await
        .is_err()
    {
        return false;
    }

    let mut response = Vec::with_capacity(256);
    if !matches!(
        tokio::time::timeout(Duration::from_secs(1), stream.read_to_end(&mut response)).await,
        Ok(Ok(_))
    ) {
        return false;
    }

    response
        .windows(b"\r\n\r\nOK".len())
        .any(|window| window == b"\r\n\r\nOK")
}

async fn terminate_child(child: &mut Child) {
    if let Some(pid) = child.id() {
        // SAFETY: kill is called with a live child PID returned by Tokio.
        unsafe {
            libc::kill(pid as libc::pid_t, libc::SIGTERM);
        }
    }
    if tokio::time::timeout(Duration::from_secs(10), child.wait())
        .await
        .is_err()
    {
        let _ = child.kill().await;
    }
}

fn restart_delay(failures: usize) -> Duration {
    RESTART_DELAYS[failures.min(RESTART_DELAYS.len() - 1)]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn discovers_first_executable_candidate() {
        let temp = std::env::temp_dir().join(format!(
            "celesto-docker-test-{}-{}",
            std::process::id(),
            std::thread::current().name().unwrap_or("unnamed")
        ));
        fs::create_dir_all(&temp).unwrap();
        let first = temp.join("first");
        let second = temp.join("second");
        fs::write(&first, b"not executable").unwrap();
        fs::write(&second, b"executable").unwrap();
        fs::set_permissions(&second, fs::Permissions::from_mode(0o755)).unwrap();

        let first = first.to_string_lossy().into_owned();
        let second = second.to_string_lossy().into_owned();
        assert_eq!(
            discover_dockerd(&[first.as_str(), second.as_str()]),
            Some(PathBuf::from(second))
        );
        fs::remove_dir_all(temp).unwrap();
    }

    #[test]
    fn restart_delay_is_bounded() {
        assert_eq!(restart_delay(0), Duration::from_secs(1));
        assert_eq!(restart_delay(2), Duration::from_secs(5));
        assert_eq!(restart_delay(100), Duration::from_secs(30));
    }
}
