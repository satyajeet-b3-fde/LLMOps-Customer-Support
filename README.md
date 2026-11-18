# LLMOps Customer Support API

FastAPI service that answers customer-support questions with Azure OpenAI, returns latency and token usage, and is deployed to Azure App Service through a GitHub Actions workflow that you run manually.

## Azure resources (resource group `rg-llmops-customer-support`, East US)

| Resource | Name |
|---|---|
| Azure OpenAI | `aoai-llmops-cs-1260` |
| Model deployment | `gpt-support-prod` (gpt-5.4-mini, GlobalStandard) |
| App Service plan | `asp-llmops-cs` (Linux, B1) |
| Web App | `llmops-cs-api-1260` → https://llmops-cs-api-1260.azurewebsites.net |
| Application Insights | `appi-llmops-cs` |

## Run locally

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env   # then fill in values
python -m pytest
python -m uvicorn app.main:app --reload --port 8000
# http://127.0.0.1:8000/docs
```

## Endpoints

- `GET /`: app status and version
- `GET /health`: health check
- `POST /chat`: body `{"question": "How can I return a product?"}`

## Deploy (GitHub Actions, manual trigger)

1. Repo → Settings → Secrets and variables → Actions:
   - Secret `AZURE_WEBAPP_PUBLISH_PROFILE`: full contents of the `.PublishSettings` file
   - Variable `AZURE_WEBAPP_NAME`: `llmops-cs-api-1260`
2. Actions → **LLMOps CI-CD Azure Deployment** → **Run workflow**.
3. Verify `/`, `/health`, `/docs`, and `POST /chat` on the live URL.

The workflow runs the tests first and deploys only if they pass. To deploy on every push, add a `push` trigger in `.github/workflows/deploy.yml`.

## Monitoring

- Logs: Web App → Monitoring → Log stream
- Telemetry: Application Insights `appi-llmops-cs`. Requests, exceptions, and `LLM request completed` traces include latency and token counts.
