from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.db.database import init_db, reset_db
from app.data.seed import seed_database
from app.api.routes import machines, work_orders, scheduling, simulation
from app.core.errors import NotFoundError, ConflictError, ValidationError, BadRequestError
from app.core.config import settings
from app.core.logging import setup_logging, logger

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    seed_database()
    logger.info("Database initialized and seeded.")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Assisted Dynamic Production Scheduler POC",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(machines.router)
app.include_router(work_orders.router)
app.include_router(scheduling.router)
app.include_router(simulation.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.post("/admin/reset", tags=["Admin"])
def reset_database():
    reset_db()
    seed_database()
    return {"message": "Database reset and seeded."}

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(BadRequestError)
async def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
