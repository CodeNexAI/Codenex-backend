# Nebius and Nemotron Integration

CodeNex Backend isolates model access behind `ModelProvider`.

## Providers

- `MockModelProvider`: local development and pytest without Nebius credentials
- `NemotronProvider`: real HTTP client for NVIDIA Nemotron through a Nebius-configured endpoint

## Required Environment Variables

- `NEBIUS_API_KEY`
- `NEBIUS_BASE_URL`
- `NEMOTRON_MODEL`

If any of these values are missing, the backend uses the mock provider instead of pretending to make a real model call.
