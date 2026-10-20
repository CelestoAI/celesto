//! Header injection rules (D-05 lock 2, D-19).
//!
//! A real value replaces a placeholder only when a header named by one of the
//! binding's rules carries exactly the placeholder in that rule's form, and
//! the request is for one of the binding's hosts. The body and URL are never
//! touched. Anything else that carries a placeholder is reported as a refusal.

use super::{Config, HeaderForm};
use base64::Engine as _;
use base64::engine::general_purpose::STANDARD as B64;
use hyper::Uri;
use hyper::header::{HeaderMap, HeaderName, HeaderValue};
use std::collections::HashSet;

pub(crate) struct Match {
    pub name: String,
    pub header: HeaderName,
    pub form: HeaderForm,
    /// Basic auth user name, kept as sent.
    pub basic_user: Option<Vec<u8>>,
}

pub(crate) struct Refusal {
    pub name: String,
    pub reason: &'static str,
}

#[derive(Default)]
pub(crate) struct Plan {
    pub matches: Vec<Match>,
    pub refusals: Vec<Refusal>,
}

fn strip_scheme<'a>(value: &'a [u8], scheme: &[u8]) -> Option<&'a [u8]> {
    let n = scheme.len();
    if value.len() > n && value[..n].eq_ignore_ascii_case(scheme) && value[n] == b' ' {
        Some(&value[n + 1..])
    } else {
        None
    }
}

fn decode_basic(value: &[u8]) -> Option<Vec<u8>> {
    B64.decode(strip_scheme(value, b"basic")?).ok()
}

/// `Some(user)` when `value` carries exactly `placeholder` in `form`.
fn matches_form(value: &[u8], form: HeaderForm, placeholder: &str) -> Option<Option<Vec<u8>>> {
    let ph = placeholder.as_bytes();
    match form {
        HeaderForm::Raw => (value == ph).then_some(None),
        HeaderForm::Bearer => (strip_scheme(value, b"bearer")? == ph).then_some(None),
        HeaderForm::BasicPassword => {
            let decoded = decode_basic(value)?;
            let colon = decoded.iter().position(|&b| b == b':')?;
            (&decoded[colon + 1..] == ph).then(|| Some(decoded[..colon].to_vec()))
        }
    }
}

fn contains(haystack: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty() && haystack.windows(needle.len()).any(|w| w == needle)
}

/// True when `placeholder` appears in the URL or in any header other than
/// those in `skip`, including inside Basic credentials.
fn seen_elsewhere(
    headers: &HeaderMap,
    uri: &Uri,
    placeholder: &str,
    skip: &HashSet<HeaderName>,
) -> bool {
    let ph = placeholder.as_bytes();
    let target = uri.path_and_query().map(|p| p.as_str()).unwrap_or("");
    if contains(target.as_bytes(), ph) {
        return true;
    }
    headers.iter().any(|(name, value)| {
        if skip.contains(name) {
            return false;
        }
        let bytes = value.as_bytes();
        contains(bytes, ph) || decode_basic(bytes).is_some_and(|d| contains(&d, ph))
    })
}

pub(crate) fn plan(config: &Config, host: &str, headers: &HeaderMap, uri: &Uri) -> Plan {
    let mut out = Plan::default();
    for binding in &config.bindings {
        let bound = binding.hosts.iter().any(|h| h == host);
        let mut injected_headers = HashSet::new();
        let mut duplicate = false;
        if bound {
            for rule in &binding.headers {
                let Ok(name) = HeaderName::from_bytes(rule.header.as_bytes()) else {
                    continue;
                };
                if injected_headers.contains(&name) {
                    continue;
                }
                let values: Vec<&HeaderValue> = headers.get_all(&name).iter().collect();
                let hits: Vec<_> = values
                    .iter()
                    .filter_map(|v| matches_form(v.as_bytes(), rule.form, &binding.placeholder))
                    .collect();
                if hits.is_empty() {
                    continue;
                }
                if values.len() > 1 {
                    // Repeated header: which copy the upstream reads is
                    // ambiguous, so inject into none of them.
                    duplicate = true;
                    continue;
                }
                injected_headers.insert(name.clone());
                out.matches.push(Match {
                    name: binding.name.clone(),
                    header: name,
                    form: rule.form,
                    basic_user: hits.into_iter().next().flatten(),
                });
            }
        }
        if duplicate {
            out.refusals.push(Refusal {
                name: binding.name.clone(),
                reason: "duplicate_header",
            });
        } else if seen_elsewhere(headers, uri, &binding.placeholder, &injected_headers) {
            out.refusals.push(Refusal {
                name: binding.name.clone(),
                reason: if bound { "wrong_place" } else { "unbound_host" },
            });
        }
    }
    out
}

/// Replace the placeholder in `m.header` with `real`. Fails if `real` cannot
/// be a header value; the header is then left unchanged.
pub(crate) fn apply(headers: &mut HeaderMap, m: &Match, real: &str) -> Result<(), ()> {
    let text = match m.form {
        HeaderForm::Raw => real.to_string(),
        HeaderForm::Bearer => format!("Bearer {real}"),
        HeaderForm::BasicPassword => {
            let mut creds = m.basic_user.clone().unwrap_or_default();
            creds.push(b':');
            creds.extend_from_slice(real.as_bytes());
            format!("Basic {}", B64.encode(creds))
        }
    };
    let mut value = HeaderValue::from_str(&text).map_err(|_| ())?;
    value.set_sensitive(true);
    headers.insert(m.header.clone(), value);
    Ok(())
}

/// Scrub every placeholder from text that goes into the log.
pub(crate) fn redact(config: &Config, text: &str) -> String {
    let mut out = text.to_string();
    for binding in &config.bindings {
        if out.contains(&binding.placeholder) {
            out = out.replace(&binding.placeholder, "[placeholder]");
        }
    }
    if out.len() > 512 {
        let mut cut = 512;
        while !out.is_char_boundary(cut) {
            cut -= 1;
        }
        out.truncate(cut);
    }
    out
}
