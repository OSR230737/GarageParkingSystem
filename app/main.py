from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.spots import router as spots_router
from app.db import create_tables

app = FastAPI(title="Garage Parking System")
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
	create_tables()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(spots_router)
app.include_router(sessions_router)