//! sysctl via direct /proc/sys writes.

use crate::error::NetlinkError;
use std::fs;
use std::path::PathBuf;

/// Write a sysctl value via /proc/sys.
///
/// Key uses dot notation (e.g., "net.ipv4.ip_forward") which is
/// converted to path notation (/proc/sys/net/ipv4/ip_forward).
pub fn write(key: &str, value: &str) -> Result<(), NetlinkError> {
    let components: Vec<_> = key.split(['.', '/']).collect();
    if components.iter().any(|component| {
        component.is_empty()
            || !component
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-'))
    }) {
        return Err(NetlinkError::Other(format!("invalid sysctl key: {key:?}")));
    }
    let mut path = PathBuf::from("/proc/sys");
    path.extend(components);

    fs::write(&path, value)
        .map_err(|e| NetlinkError::Other(format!("sysctl write {} = {}: {}", key, value, e)))?;

    log::debug!("sysctl {} = {}", key, value);
    Ok(())
}

/// Allow localhost DNAT traffic to route through a TAP interface.
pub fn write_tap_route_localnet(name: &str) -> Result<(), NetlinkError> {
    write(&format!("net/ipv4/conf/{name}/route_localnet"), "1")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn invalid_sysctl_keys_cannot_overwrite_other_files() {
        let victim = std::env::temp_dir().join(format!("celesto-sysctl-{}", std::process::id()));
        fs::write(&victim, "keep").unwrap();
        let result = write(victim.to_str().unwrap(), "overwritten");
        let contents = fs::read_to_string(&victim).unwrap();
        fs::remove_file(victim).unwrap();
        assert!(result.is_err(), "absolute key was accepted");
        assert_eq!(contents, "keep");
        for key in [
            "",
            ".",
            "..",
            "/",
            "net..ipv4",
            "net//ipv4",
            "net/../ipv4",
            "net/ipv4/",
            "net.ipv4.\0forward",
        ] {
            let error = write(key, "1").unwrap_err();
            assert!(
                error.to_string().contains("invalid sysctl key"),
                "{key:?}: {error}"
            );
        }
    }
}
