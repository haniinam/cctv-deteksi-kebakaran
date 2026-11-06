import json
import os
from datetime import datetime
from pathlib import Path

from config import LATEST_FILE, LOGS_DIR

DATABASE_URL = os.environ.get("DATABASE_URL")


class OutputManager:

    def __init__(self, camera):
        self.camera = camera
        self.base_dir = Path(__file__).resolve().parent
        self.logs_dir = self.base_dir / LOGS_DIR
        self.logs_dir.mkdir(exist_ok=True)
        self.latest_path = self.base_dir / LATEST_FILE

        self.db = None
        if DATABASE_URL:
            from db import Database
            self.db = Database(DATABASE_URL)

    def generate(self, fire_result):
        return {
            "module": "fire",
            "camera_id": self.camera["id"],
            "camera_name": self.camera.get("name"),
            "location": self.camera.get("location"),
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "fire": fire_result,
        }

    def save_json(self, data):
        # 1. JSON terbaru (atomic: tidak pernah terbaca setengah jadi oleh API/dashboard)
        tmp = self.latest_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, self.latest_path)

        # 2. Riwayat: satu baris JSON per snapshot, satu file per hari
        history = self.logs_dir / f"fire_{datetime.now():%Y%m%d}.jsonl"
        with open(history, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

        # 3. Database (jika DATABASE_URL diisi); gagal simpan tidak menghentikan worker
        if self.db:
            try:
                self.db.save(data)
            except Exception as e:
                print(f"Gagal simpan ke database: {e}", flush=True)

    def display(self, data):
        f = data["fire"]
        print(
            f"[{data['timestamp']}] {data['camera_id']} | status={f['cluster_level']} | "
            f"titik_api={f['total_detections']} | klaster={f['total_clusters']} | luas={f['fire_area']} px",
            flush=True,
        )
