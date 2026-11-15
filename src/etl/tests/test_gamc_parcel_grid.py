import io

import numpy as np
from PIL import Image

from src.etl import gamc_parcel_grid as grid

BLUE = (51, 136, 255, 255)
SALMON = (244, 114, 89, 179)
GREEN = (112, 242, 46, 179)
PURPLE = (107, 74, 188, 38)


def image(size, paint):
    arr = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    arr[:] = PURPLE
    for (x0, y0, x1, y1), color in paint:
        arr[y0:y1, x0:x1] = color
    return Image.fromarray(arr, "RGBA")


def test_pixels_are_classified_by_their_layer_colour():
    arr = np.array([[BLUE, SALMON, GREEN, PURPLE]], dtype=np.uint8)
    drain, urban = grid.classify(arr)
    assert drain.tolist() == [[True, False, False, False]]
    assert urban.tolist() == [[0, 1, 2, 0]]


def test_distance_to_the_nearest_channel_in_metres():
    # 100 px wide, 10 m per pixel: a channel column at x=0 and one cell 50 px away.
    drain = np.zeros((20, 100), dtype=bool)
    drain[:, 0] = True
    metres = grid.channel_distance(drain, cell_px=10, px_m=(10.0, 10.0))
    assert metres[0][0] <= 60
    assert metres[0][5] == 550
    assert metres[0][9] == grid.CAP_M


def test_zone_grid_encodes_and_looks_up_a_point():
    img = image((200, 200), [((90, 0, 110, 200), BLUE), ((0, 0, 60, 60), SALMON)])
    entry = grid.zone_grid(img, bbox=[-66.30, -17.50, -66.28, -17.48], cell_px=10)
    assert (entry["cols"], entry["rows"]) == (20, 20)
    near = grid.lookup(entry, lat=-17.49, lon=-66.29)
    assert near["canal_m"] <= 20
    far = grid.lookup(entry, lat=-17.49, lon=-66.2985)
    assert far["canal_m"] > 100
    urban = grid.lookup(entry, lat=-17.4825, lon=-66.2985)
    assert urban["periurbano"] == "consolidado"
    assert grid.lookup(entry, lat=0, lon=0) is None


def test_run_writes_one_entry_per_zone(tmp_path):
    zones = tmp_path / "zonas"
    zones.mkdir()
    buf = io.BytesIO()
    image((100, 100), []).save(buf, format="PNG")
    (zones / "D9_itocta.png").write_bytes(buf.getvalue())
    (zones / "index.json").write_text(
        '{"zonas": {"D9_itocta": {"bbox": [-66.3, -17.5, -66.28, -17.48], "width": 100, "height": 100}}}'
    )
    out = grid.run(zones, cell_px=10)
    assert set(out["zonas"]) == {"D9_itocta"}
    assert (zones / "grid.json").exists()
