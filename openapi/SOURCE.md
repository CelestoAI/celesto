# Cloud API snapshot

`cloud.json` is the full FastAPI document exported from `CelestoAI/backend` at
commit `1d98dd0a3b49a9d01789fea71d11e06adb9f6c96` and formatted with
`python -m json.tool`. That backend follow-up corrects computer validation-error
and streaming response documentation; it does not change runtime behavior.

SHA256: `381a8f345ce7287bb0c86557cadc44210ab3b72117f9c0713becf11971b671d7`

Generator: `openapi-python-client==0.29.1`, configured by `python-client.yaml`;
formatter: `ruff==0.15.6` with isolated configuration.
Run `bash scripts/generate_cloud_client.sh` from the repository root to rebuild
the private client. The full API is generated, including internal endpoints;
only the handwritten public `Computer` wrapper is supported for users.
