//! Fresh per-start CA held only in memory (D-14).

use super::ProxyError;
use rcgen::{
    BasicConstraints, CertificateParams, CertifiedIssuer, DnType, ExtendedKeyUsagePurpose, IsCa,
    KeyPair, KeyUsagePurpose,
};
use rustls::pki_types::{CertificateDer, PrivateKeyDer, PrivatePkcs8KeyDer};
use rustls::server::ServerConfig;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use time::{Duration, OffsetDateTime};

pub(crate) struct Ca {
    issuer: CertifiedIssuer<'static, KeyPair>,
    cert_pem: String,
    leaves: Mutex<HashMap<String, Arc<ServerConfig>>>,
}

fn tls_err(e: impl std::fmt::Display) -> ProxyError {
    ProxyError::Tls(e.to_string())
}

fn random_hex(bytes: usize) -> Result<String, ProxyError> {
    let mut buf = vec![0u8; bytes];
    rustls::crypto::ring::default_provider()
        .secure_random
        .fill(&mut buf)
        .map_err(|_| ProxyError::Tls("no secure random source".into()))?;
    Ok(buf.iter().map(|b| format!("{b:02x}")).collect())
}

pub(crate) fn provider() -> Arc<rustls::crypto::CryptoProvider> {
    Arc::new(rustls::crypto::ring::default_provider())
}

impl Ca {
    pub fn generate() -> Result<Self, ProxyError> {
        let mut params = CertificateParams::new(Vec::<String>::new()).map_err(tls_err)?;
        params.is_ca = IsCa::Ca(BasicConstraints::Constrained(0));
        params.distinguished_name.push(
            DnType::CommonName,
            format!("Celesto sandbox CA {}", random_hex(4)?),
        );
        params
            .distinguished_name
            .push(DnType::OrganizationName, "Celesto");
        params.key_usages = vec![KeyUsagePurpose::KeyCertSign, KeyUsagePurpose::CrlSign];
        let now = OffsetDateTime::now_utc();
        params.not_before = now - Duration::days(1);
        params.not_after = now + Duration::days(3650);
        let key = KeyPair::generate().map_err(tls_err)?;
        let issuer = CertifiedIssuer::self_signed(params, key).map_err(tls_err)?;
        let cert_pem = issuer.pem();
        Ok(Ca {
            issuer,
            cert_pem,
            leaves: Mutex::new(HashMap::new()),
        })
    }

    pub fn cert_pem(&self) -> &str {
        &self.cert_pem
    }

    /// TLS server config with a leaf for `host`, minted once per host.
    pub fn server_config(&self, host: &str) -> Result<Arc<ServerConfig>, ProxyError> {
        let mut leaves = self.leaves.lock().unwrap_or_else(|e| e.into_inner());
        if let Some(config) = leaves.get(host) {
            return Ok(config.clone());
        }
        let mut params = CertificateParams::new(vec![host.to_string()]).map_err(tls_err)?;
        params.distinguished_name.push(DnType::CommonName, host);
        params.is_ca = IsCa::ExplicitNoCa;
        params.key_usages = vec![KeyUsagePurpose::DigitalSignature];
        params.extended_key_usages = vec![ExtendedKeyUsagePurpose::ServerAuth];
        params.use_authority_key_identifier_extension = true;
        let now = OffsetDateTime::now_utc();
        params.not_before = now - Duration::days(1);
        params.not_after = now + Duration::days(397);
        let key = KeyPair::generate().map_err(tls_err)?;
        let cert = params.signed_by(&key, &self.issuer).map_err(tls_err)?;
        let chain: Vec<CertificateDer<'static>> =
            vec![cert.der().clone(), self.issuer.der().clone()];
        let key_der = PrivateKeyDer::Pkcs8(PrivatePkcs8KeyDer::from(key.serialize_der()));
        let mut config = ServerConfig::builder_with_provider(provider())
            .with_safe_default_protocol_versions()
            .map_err(tls_err)?
            .with_no_client_auth()
            .with_single_cert(chain, key_der)
            .map_err(tls_err)?;
        config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];
        let config = Arc::new(config);
        leaves.insert(host.to_string(), config.clone());
        Ok(config)
    }
}
