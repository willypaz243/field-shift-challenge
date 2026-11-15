from fastapi import FastAPI

from api.core.errors import install_error_handlers
from api.core.http import install_http_middleware
from api.modules.alerts.router import router as alerts_router
from api.modules.climate.router import router as climate_router
from api.modules.crops.router import router as crops_router
from api.modules.feedback.router import router as feedback_router
from api.modules.reports.router import router as reports_router
from api.modules.sync.router import router as sync_router
from api.modules.water.router import router as water_router
from api.modules.zones.router import router as zones_router


def create_app() -> FastAPI:
    app = FastAPI(title="Choclito API")
    install_error_handlers(app)
    install_http_middleware(app)
    for router in (
        zones_router,
        crops_router,
        climate_router,
        alerts_router,
        feedback_router,
        reports_router,
        sync_router,
        water_router,
    ):
        app.include_router(router)
    return app


app = create_app()
