# API

FastAPI modular monolith. Architecture and stack: see the root [`README.md`](../README.md).

## Contract

[`openapi.yaml`](openapi.yaml) is the machine-readable version of [`docs/API-CONTRACT.md`](../docs/API-CONTRACT.md). Both change together in the same PR.

Every response has an example taken from the contract, so the mock returns realistic data.

## Mock server

Run the contract as a fake API (no Python needed):

```bash
npx @stoplight/prism-cli@5 mock api/openapi.yaml -p 4010
```

```bash
curl http://localhost:4010/zones
curl "http://localhost:4010/sync?zone_id=D9_itocta"
```

POST endpoints validate the request body against the contract and answer with the example response.

## Pointing the app to the mock or the real API

The app reads the base URL from one setting:

| Target | Base URL |
|---|---|
| Mock on the same computer (web, iOS simulator) | `http://localhost:4010` |
| Mock from an Android phone or emulator | `http://<your-computer-LAN-IP>:4010` (emulator: `http://10.0.2.2:4010`) |
| FastAPI | `http://localhost:8000` (or the LAN IP) |

Switching from the mock to FastAPI only changes that URL.

## Checking the spec

```bash
uvx openapi-spec-validator api/openapi.yaml
```
