
from fastapi import FastAPI
from src.api.v1.accounts import router as accounts_router
from src.core.config import settings

from src.api.v1.api import api_router
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)
app.include_router(api_router)




if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
