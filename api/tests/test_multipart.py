import httpx
import pytest

from api.core.errors import ApiError
from api.core.multipart import MAX_BODY_BYTES, parse_form


def encode(data, files=None):
    request = httpx.Request("POST", "http://test", data=data, files=files)
    return request.headers["content-type"], request.read()


def test_binary_files_keep_every_byte():
    blob = bytes(range(256)) * 4 + b"\r\n\r\n--boundary\n\r\r\n"

    fields, files = parse_form(*encode({"tipo": "helada"}, {"foto": ("f.jpg", blob, "image/jpeg")}))

    assert fields == {"tipo": "helada"}
    assert files == {"foto": ("image/jpeg", blob)}


def test_url_encoded_forms_are_accepted():
    assert parse_form(*encode({"tipo": "granizo"})) == ({"tipo": "granizo"}, {})


def test_a_body_over_the_limit_is_rejected():
    with pytest.raises(ApiError):
        parse_form("multipart/form-data; boundary=x", b"0" * (MAX_BODY_BYTES + 1))
