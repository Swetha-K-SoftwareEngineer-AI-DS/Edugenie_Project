import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.database import create_tables, engine, is_sqlite_mode
from backend.ai_service import ai_service
from backend.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("edugenie.main")

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    logger.info("Starting up EduGenie – AI Educational Assistant (v%s)...", settings.APP_VERSION)
    try:
        create_tables()
        logger.info("Database schema initialized. Mode: %s", "SQLite Fallback" if is_sqlite_mode else "MySQL")
    except Exception as e:
        logger.error("Database initialization notice: %s", str(e))
    yield
    logger.info("EduGenie application shutting down.")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Full-stack educational AI assistant for students with question answering, quiz generation, summarization, and personalized learning roadmaps.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach state & rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for seamless frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development and browser fetch
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler (Never expose raw stack traces to users)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error processing %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later."}
    )


# Health Check Endpoint
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def check_health():
    """
    Health check endpoint returning system, database, and AI status.
    """
    db_ok = True
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        database_connected=db_ok,
        gemini_configured=ai_service.is_configured
    )


# Include API Route modules
from backend.routes.chat import router as chat_router, ask_educational_question
from backend.routes.quiz import router as quiz_router
from backend.routes.summary import router as summary_router
from backend.routes.learning import router as learning_router, create_personalized_learning_path
from backend.routes.activity import router as activity_router
from backend.schemas import ChatResponse, LearningPathResponse

app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(summary_router)
app.include_router(learning_router)
app.include_router(activity_router)

# Architecture alias routes reusing existing implementations
app.add_api_route(
    "/api/qa",
    ask_educational_question,
    methods=["POST"],
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Q&A"],
    summary="Q&A Module (Architecture alias for /api/chat)"
)

app.add_api_route(
    "/api/explain",
    ask_educational_question,
    methods=["POST"],
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explanation"],
    summary="Explanation Module (Architecture alias for /api/chat)"
)

app.add_api_route(
    "/api/learn/recommendations",
    create_personalized_learning_path,
    methods=["POST"],
    response_model=LearningPathResponse,
    status_code=status.HTTP_200_OK,
    tags=["Learning Recommendations"],
    summary="Learning Recommendations Module (Architecture alias for /api/learning-path)"
)

# Mount frontend directory for direct serving
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
