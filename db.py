# ==================================
# PENYIMPANAN KE DATABASE (opsional)
# Aktif jika env DATABASE_URL diisi, contoh:
#   postgresql+psycopg2://user:pass@host:5432/cctv
#   sqlite:///fire.db
# ==================================

from datetime import datetime

from sqlalchemy import (
    JSON, Column, DateTime, Index, Integer, MetaData, String, Table, create_engine,
)

metadata = MetaData()

fire_snapshots = Table(
    "fire_snapshots", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("module", String(32), nullable=False),
    Column("camera_id", String(64), nullable=False),
    Column("location", String(128)),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("level_code", Integer, nullable=False),         # 1 aman, 2 sedang, 3 bahaya
    Column("cluster_level", String(32), nullable=False),   # Aman / Level 2 / Level 3 / Level 3 (Bahaya)
    Column("total_detections", Integer, nullable=False),
    Column("total_clusters", Integer, nullable=False),
    Column("fire_area", Integer, nullable=False),          # total luas kotak api (piksel)
    Column("detections", JSON, nullable=False),
    Index("ix_fire_camera_time", "camera_id", "timestamp"),
)


class Database:

    def __init__(self, url):
        # pool_pre_ping: koneksi yang diputus server dibuka ulang otomatis
        self.engine = create_engine(url, pool_pre_ping=True)
        metadata.create_all(self.engine)

    def save(self, data):
        f = data["fire"]
        with self.engine.begin() as conn:
            conn.execute(fire_snapshots.insert(), {
                "module": data["module"],
                "camera_id": data["camera_id"],
                "location": data.get("location"),
                "timestamp": datetime.fromisoformat(data["timestamp"]),
                "level_code": f["level_code"],
                "cluster_level": f["cluster_level"],
                "total_detections": f["total_detections"],
                "total_clusters": f["total_clusters"],
                "fire_area": f["fire_area"],
                "detections": f["detections"],
            })
