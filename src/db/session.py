from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from core.config import settings


engine = create_async_engine(
    url=settings.DATABASE_URL,
)

SessionLocal = async_sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    bind=engine
)


async def get_db():
    async with SessionLocal() as db:
        yield db
