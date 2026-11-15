from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, codigo: str, mensaje_tecnico: str) -> None:
        super().__init__(mensaje_tecnico)
        self.status_code = status_code
        self.codigo = codigo
        self.mensaje_tecnico = mensaje_tecnico


def _error(status_code: int, codigo: str, mensaje_tecnico: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"codigo": codigo, "mensaje_tecnico": mensaje_tecnico}},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error(exc.status_code, exc.codigo, exc.mensaje_tecnico)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return _error(400, "invalid_request", str(exc.errors()[0].get("msg", "invalid request")))
