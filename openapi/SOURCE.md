# Cloud API snapshot

`cloud.json` is the full FastAPI document exported from `CelestoAI/backend` at
commit `6cd23663ab0ed0e104cd5c9117ce78bfe598d5f4` and formatted with
`python -m json.tool`. The snapshot was verified against that revision's
`app.openapi()` output.

SHA256: `cf5d9b58ddba24c3f9952b36240348f5380b1e050d46b3a637a5e7b56c057c5a`

Generator: `openapi-python-client==0.29.1`, configured by `python-client.yaml`;
formatter: `ruff==0.15.6` with isolated configuration.
Run `bash scripts/generate_cloud_client.sh` from the repository root to rebuild
the private client. The full API is generated, including internal endpoints;
only the handwritten public `Computer` and `Template` wrappers are supported
for users.

`python-client.yaml` renames three GitHub Actions cache responses whose
generated file names would exceed the 255-byte file-name limit.
