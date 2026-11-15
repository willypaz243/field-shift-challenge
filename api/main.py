from fastapi import FastAPI

from api.modules.feedback.router import router as feedback_router


def create_app() -> FastAPI:
    app = FastAPI(title="Choclito API")
    app.include_router(feedback_router)
    return app


app = create_app()
