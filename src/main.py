from fastapi import FastAPI
from fastapi.security import HTTPBearer

from src.core.config import settings
from src.api.v1.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

bearer_scheme = HTTPBearer()
app.openapi_schema = None
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
