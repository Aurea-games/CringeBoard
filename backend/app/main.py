from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os


def get_cors_origins():
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="CringeBoard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "CringeBoard API", "status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

