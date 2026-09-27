# Cloud API snapshot

`cloud.json` is the full FastAPI document exported from `CelestoAI/backend` at
commit `1af5e206df916b57bb596cf71f951a30697a8d2a` and formatted with
`python -m json.tool`. The snapshot was verified against that revision's
`app.openapi()` output.

SHA256: `051119064f71a68dd25fdc7e37146334d2b5b4c38b629083c53fbe65d8390b46`

Generator: `openapi-python-client==0.29.1`, configured by `python-client.yaml`;
formatter: `ruff==0.15.6` with isolated configuration.
Run `bash scripts/generate_cloud_client.sh` from the repository root to rebuild
the private client. The full API is generated, including internal endpoints;
only the handwritten public `Computer` wrapper is supported for users.
