from email.parser import BytesParser
from email.policy import HTTP
from urllib.parse import parse_qsl

from api.core.errors import ApiError

# Enough for a 300 KB photo plus a 60 s audio clip and the text fields.
MAX_BODY_BYTES = 2_000_000


def parse_form(
    content_type: str, body: bytes
) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    """Split a form body into text fields and files (content type, bytes).

    Uses the standard library so the API does not need python-multipart.
    """
    if len(body) > MAX_BODY_BYTES:
        raise ApiError(400, "invalid_request", f"body larger than {MAX_BODY_BYTES} bytes")
    if content_type.startswith("application/x-www-form-urlencoded"):
        return dict(parse_qsl(body.decode())), {}
    if not content_type.startswith("multipart/form-data"):
        raise ApiError(400, "invalid_request", "expected multipart/form-data")
    message = BytesParser(policy=HTTP).parsebytes(
        b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + body
    )
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        payload = part.get_payload(decode=True) or b""
        if not isinstance(name, str):
            continue
        if part.get_filename() is None:
            fields[name] = payload.decode()
        else:
            files[name] = (part.get_content_type(), payload)
    return fields, files
