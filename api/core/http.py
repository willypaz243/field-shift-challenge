import hashlib
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class ETagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method != "GET" or response.status_code != 200:
            return response
        body = b"".join([chunk async for chunk in response.body_iterator])
        etag = f'W/"{hashlib.sha256(body).hexdigest()[:32]}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
        headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
        headers["ETag"] = etag
        if headers.get("content-type") == "application/json":
            headers["content-type"] = "application/json; charset=utf-8"
        return Response(body, status_code=200, headers=headers, media_type=response.media_type)


def install_http_middleware(app: FastAPI) -> None:
    app.add_middleware(ETagMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=500)
    origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"]
    )
