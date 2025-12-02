from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import auth, stacks, agents
from app.database import engine, Base
from app.utils import aegra_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure aegra.json directory and file exist at startup
    aegra_json.ensure_aegra_json_exists()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Stack & Agent Management API",
    description="API for managing stacks and agents",
    version="0.1.0",
    lifespan=lifespan,
)

origins = settings.cors_origins.split(",") if "," in settings.cors_origins else [settings.cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stacks.router)
app.include_router(agents.router)


@app.get("/")
async def root():
    return {"message": "Stack & Agent Management API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

