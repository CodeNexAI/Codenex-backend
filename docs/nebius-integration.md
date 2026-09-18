# Nebius Token Factory and NVIDIA Nemotron

`NebiusNemotronProvider` implements the `ModelProvider` interface without
exposing provider details to agents. It uses the documented Nebius Token Factory
OpenAI-compatible chat-completions API:

- Base URL: `https://api.tokenfactory.nebius.com/v1`
- Endpoint: `POST /chat/completions`
- Authentication: `Authorization: Bearer <NEBIUS_API_KEY>`
- Response text: `choices[0].message.content`

The configured `NEMOTRON_MODEL` value is sent as the `model` request field.
Choose a model that is available to the Nebius project; CodeNex does not
hard-code or select a model.

## Configuration

Set these variables in an uncommitted `.env` file:

```dotenv
NEBIUS_API_KEY=your_api_key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEMOTRON_MODEL=your_available_nemotron_model
```

If the API key or model is absent, CodeNex uses `MockModelProvider`. The mock is
only for local development and tests; it makes no network calls and is not a
model integration.

## Integration testing

Integration tests are intentionally not part of `pytest` and require a real,
uncommitted API key and a Nebius-available Nemotron model:

1. Copy `.env.example` to `.env`.
2. Set `NEBIUS_API_KEY` and `NEMOTRON_MODEL`.
3. Verify a minimal chat-completions request in an isolated development
   environment before enabling it in a deployed service.

Never log, commit, or return `NEBIUS_API_KEY`.
