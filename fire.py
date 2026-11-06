# ==================================
# DETEKSI & KLASTERISASI API
# Logika sama dengan fire_pipeline_live.py (_run_detection dan verifikasi
# Level 3 selama 5 detik), tanpa IPython/requests agar bisa jalan di server.
# Waktu Level 3 memakai waktu video, bukan jam dinding.
# ==================================

import numpy as np
from sklearn.cluster import DBSCAN
from ultralytics import YOLO

from config import (
    CONFIDENCE, DANGER_SECONDS, EPS_DISTANCE, IMAGE_SIZE, LEVEL2_AREA, LEVEL3_AREA, MODEL_PATH,
)


class FireDetector:

    def __init__(self):
        self.model = YOLO(MODEL_PATH, task="detect")
        self.level3_since = None
        print("YOLO Model Loaded")

    def detect(self, frame, t):
        """Mengembalikan hasil satu frame: level, jumlah titik api/klaster, dan kotak api."""
        r = self.model.predict(frame, conf=CONFIDENCE, imgsz=IMAGE_SIZE, verbose=False)[0]
        result = {"level_code": 1, "cluster_level": "Aman", "total_detections": 0,
                  "total_clusters": 0, "fire_area": 0, "detections": []}

        if r.boxes is not None and len(r.boxes):
            boxes = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            centroids = np.column_stack(((boxes[:, 0] + boxes[:, 2]) / 2, (boxes[:, 1] + boxes[:, 3]) / 2))
            area = float(((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])).sum())
            labels = (DBSCAN(eps=EPS_DISTANCE, min_samples=1).fit(centroids).labels_
                      if len(boxes) > 1 else np.array([0]))

            if area > LEVEL3_AREA:
                result.update(level_code=3, cluster_level="Level 3")
            elif area > LEVEL2_AREA:
                result.update(level_code=2, cluster_level="Level 2")
            result.update(total_detections=len(boxes), total_clusters=len(set(labels)),
                          fire_area=int(area))
            result["detections"] = [
                {"class_name": "fire", "confidence": round(float(c), 4), "cluster_id": int(l),
                 "bbox": [int(v) for v in b]}
                for b, c, l in zip(boxes, confs, labels)
            ]

        # Level 3 berturut-turut lebih dari DANGER_SECONDS -> Bahaya (mencegah false positive)
        if result["level_code"] == 3:
            self.level3_since = t if self.level3_since is None else self.level3_since
            if t - self.level3_since > DANGER_SECONDS:
                result["cluster_level"] = "Level 3 (Bahaya)"
        else:
            self.level3_since = None
        return result
