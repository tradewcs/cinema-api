from fastapi import FastAPI

from src.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
