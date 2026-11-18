import os
import time
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from openai import AzureOpenAI

# Local .env wins over machine-level variables; in Azure there is no .env,
# so App Service environment variables are used.
load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llmops")

# Send logs/requests/exceptions to Application Insights when running in Azure
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(logger_name="llmops")
    except Exception:  # never block startup because of telemetry
        logger.exception("Application Insights setup failed")

APP_VERSION = "1.0.0"

app = FastAPI(
    title="LLMOps Customer Support API",
    description="AI customer support using Azure OpenAI",
    version=APP_VERSION,
)

SYSTEM_PROMPT = (
    "You are an enterprise customer support AI assistant. "
    "Answer professionally. Do not invent company policies. "
    "If you do not know, say the information is unavailable "
    "and recommend contacting customer support."
)


def get_client() -> AzureOpenAI:
    return AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
def home():
    return {
        "application": "LLMOps Customer Support",
        "status": "running",
        "version": APP_VERSION,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/chat")
def chat(request: ChatRequest):
    start_time = time.time()
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.question},
            ],
            # GPT-5 family models only accept the default temperature, so it is not set here.
        )
        answer = response.choices[0].message.content
        elapsed = round(time.time() - start_time, 2)
        usage = response.usage

        logger.info(
            "LLM request completed | latency=%s | prompt_tokens=%s | completion_tokens=%s | total_tokens=%s",
            elapsed, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )

        return {
            "question": request.question,
            "answer": answer,
            "latency_seconds": elapsed,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }
    except Exception:
        logger.exception("LLM request failed")
        raise HTTPException(status_code=500, detail="AI service request failed")
