from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health

app = FastAPI(
    title="Whedifaqaui",
    description="Video Knowledge Management System",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])


@app.get("/")
def root():
    """Root endpoint with basic info."""
    return {
        "app": "Whedifaqaui",
        "version": "0.1.0",
        "docs": "/docs",
    }
