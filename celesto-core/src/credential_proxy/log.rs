//! JSON-lines event log (D-18). Never contains real values or placeholders.

use serde::Serialize;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::sync::Mutex;

pub(crate) fn now_rfc3339() -> String {
    time::OffsetDateTime::now_utc()
        .format(&time::format_description::well_known::Rfc3339)
        .unwrap_or_default()
}

#[derive(Serialize, Default)]
pub(crate) struct Event<'a> {
    pub ts: String,
    pub event: &'a str,
    pub name: Option<&'a str>,
    pub host: Option<&'a str>,
    pub method: Option<&'a str>,
    pub path: Option<&'a str>,
    pub status: Option<u16>,
    pub reason: Option<&'a str>,
}

pub(crate) struct Logger {
    path: PathBuf,
    file: Mutex<Option<File>>,
}

impl Logger {
    pub fn new(path: PathBuf) -> Self {
        Logger {
            path,
            file: Mutex::new(None),
        }
    }

    pub fn open(&self) -> std::io::Result<()> {
        let mut options = OpenOptions::new();
        options.create(true).append(true);
        #[cfg(unix)]
        {
            use std::os::unix::fs::OpenOptionsExt;
            options.mode(0o600);
        }
        let file = options.open(&self.path)?;
        *self.file.lock().unwrap_or_else(|e| e.into_inner()) = Some(file);
        Ok(())
    }

    pub fn close(&self) {
        *self.file.lock().unwrap_or_else(|e| e.into_inner()) = None;
    }

    /// Write one event. Callers pass only names, hosts, methods, and paths
    /// that have already been scrubbed of placeholders (see `inject::redact`).
    pub fn write(&self, mut event: Event<'_>) {
        event.ts = now_rfc3339();
        let Ok(mut line) = serde_json::to_vec(&event) else {
            return;
        };
        line.push(b'\n');
        if let Some(file) = self.file.lock().unwrap_or_else(|e| e.into_inner()).as_mut() {
            let _ = file.write_all(&line);
        }
    }
}
