# ==================================
# OVERLAY UNTUK DASHBOARD GABUNGAN
# Tiap frame yang diproses, worker menulis hasil deteksi terbarunya ke
# logs/overlay.json (koordinat relatif 0..1). Dashboard membaca file ini dari
# ketiga bidang lalu menggambar semuanya di satu video.
# File ini sama persis di modul kemacetan, kecelakaan, dan kebakaran.
# ==================================

import json
import os
import time
from pathlib import Path

import cv2

OVERLAY_DIR = Path(__file__).resolve().parent / "logs"
OVERLAY_FILE = OVERLAY_DIR / "overlay.json"
FRAME_WIDTH = 1280
_slot = 0


def _write_frame(frame):
    """Simpan frame yang dianalisis (JPEG) bergantian ke 2 file, supaya dashboard
    selalu membaca frame yang sama dengan kotak di overlay.json."""
    global _slot
    _slot = 1 - _slot
    h, w = frame.shape[:2]
    if w > FRAME_WIDTH:
        frame = cv2.resize(frame, (FRAME_WIDTH, int(h * FRAME_WIDTH / w)))
    name = f"frame_{_slot}.jpg"
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    if not ok:
        return None
    tmp = OVERLAY_DIR / (name + ".tmp")
    tmp.write_bytes(buf.tobytes())
    os.replace(tmp, OVERLAY_DIR / name)
    return name


def publish(module, shape, status, detail, level, boxes=(), lines=(), frame=None):
    """
    status/detail: teks status (mis. "LANCAR", "82% normal")
    level        : 0 aman/lancar, 1 waspada/ramai, 2 bahaya/macet
    boxes        : [((x1, y1, x2, y2) piksel, label, (b, g, r)), ...]
    lines        : [([(x, y), ...] piksel, tertutup?, (b, g, r)), ...]
    frame        : frame yang dianalisis (opsional); dipakai dashboard sebagai video
    """
    h, w = shape[:2]
    data = {
        "module": module,
        "updated": time.time(),
        "frame": _write_frame(frame) if frame is not None else None,
        "status": status, "detail": detail, "level": level,
        "boxes": [{"xyxy": [x1 / w, y1 / h, x2 / w, y2 / h], "label": label, "color": list(color)}
                  for (x1, y1, x2, y2), label, color in boxes],
        "lines": [{"pts": [[x / w, y / h] for x, y in pts], "closed": closed, "color": list(color)}
                  for pts, closed, color in lines],
    }
    tmp = OVERLAY_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, OVERLAY_FILE)
