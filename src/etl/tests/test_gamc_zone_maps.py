import io
import json

from PIL import Image

from src.etl import gamc_zone_maps as gzm


def png(color):
    out = io.BytesIO()
    Image.new("RGBA", (4, 4), color).save(out, format="PNG")
    return out.getvalue()


class FakeResponse:
    def __init__(self, status, content=b"", ctype="image/png"):
        self.status_code = status
        self.content = content
        self.headers = {"content-type": ctype}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_window_keeps_ground_pixels_square():
    bbox, w, h = gzm.window(-17.4611, -66.2185)
    assert bbox == [-66.2485, -17.4911, -66.1885, -17.4311]
    assert (w, h) == (768, 805)


def test_run_composites_layers_and_skips_done_zones(tmp_path):
    calls = []

    def get(url, params, headers, timeout):
        calls.append(params["service_id"])
        if len(calls) == 1:
            return FakeResponse(429)
        return FakeResponse(200, png((10, 20, 200, 128)))

    zones = {"D9_itocta": {"lat": -17.4611, "lon": -66.2185}}
    index = gzm.run(zones, tmp_path, get, "k", sleep=lambda s: None)

    assert index["zonas"]["D9_itocta"]["width"] == 768
    assert (tmp_path / "D9_itocta.png").exists()
    assert len(calls) == 4  # one retry after 429, then the three layers
    assert json.loads((tmp_path / "index.json").read_text())["fuente"].startswith("GAMC WMS")

    gzm.run(zones, tmp_path, get, "k", sleep=lambda s: None)
    assert len(calls) == 4


def test_app_index_imports_every_zone_image():
    ts = gzm.app_index(["D3_molle", "D9_itocta"])
    assert 'import map_d9_itocta from "../../../data/gamc/04/zonas/D9_itocta.png";' in ts
    assert "  D3_molle: map_d3_molle," in ts
    assert gzm.app_index([]).endswith("= {};\n")
