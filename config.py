# ==================================
# CCTV FIRE DETECTION CONFIG
# Nilai default di bawah bisa dioverride lewat environment variable
# bernama sama (di Docker: file .env). Pengaturan per kamera ada di
# data/cameras.json.
# ==================================

import os


def _env(name, default):
    """Baca env var, dikonversi ke tipe default; kosong/tidak ada -> default."""
    v = os.environ.get(name)
    return default if v in (None, "") else type(default)(v)


# Daftar kamera
CAMERAS_FILE = _env("CAMERAS_FILE", "data/cameras.json")

# Model (folder OpenVINO untuk server CPU, atau file .pt untuk server GPU)
MODEL_PATH = _env("MODEL_PATH", "models/fire_openvino_model")   # dari best_v3.pt, kelas: fire
IMAGE_SIZE = _env("IMAGE_SIZE", 640)
CONFIDENCE = _env("CONFIDENCE", 0.45)

# Klasterisasi titik api (DBSCAN): titik api yang pusatnya berjarak < EPS piksel = satu klaster
EPS_DISTANCE = _env("EPS_DISTANCE", 120)

# Tingkat bahaya dari total luas kotak api (piksel, pada frame 1920x1080)
LEVEL2_AREA = _env("LEVEL2_AREA", 10000)    # > 10.000 px  -> Level 2
LEVEL3_AREA = _env("LEVEL3_AREA", 40000)    # > 40.000 px  -> Level 3
DANGER_SECONDS = _env("DANGER_SECONDS", 5)  # Level 3 berturut-turut > 5 detik -> Level 3 (Bahaya)

# Penyimpanan
SAVE_INTERVAL = _env("SAVE_INTERVAL", 10)       # detik
LATEST_FILE = "logs/fire_data.json"
LOGS_DIR = "logs"        # satu file JSONL per hari: fire_YYYYMMDD.jsonl
# Database: lihat env DATABASE_URL di output.py / db.py

# Stream
# Frame yang dianalisis per detik video. Api tidak bergerak cepat, 1 cukup
# untuk laptop CPU; di server bisa dinaikkan.
PROCESS_FPS = _env("PROCESS_FPS", 1)
RECONNECT_DELAY = _env("RECONNECT_DELAY", 2)    # detik
