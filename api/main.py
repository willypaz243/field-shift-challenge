from fastapi import FastAPI

from api.core.errors import install_error_handlers
from api.modules.feedback.router import router as feedback_router


def create_app() -> FastAPI:
    app = FastAPI(title="Choclito API")
    install_error_handlers(app)
    app.include_router(feedback_router)
    return app


app = create_app()
