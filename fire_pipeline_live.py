import os
import time
import json
import cv2
import numpy as np
import requests
from sklearn.cluster import DBSCAN
from ultralytics import YOLO
from IPython.display import display, Image

def _run_detection(frame, model, conf_threshold, eps_distance):
    results = model.predict(frame, conf=conf_threshold, verbose=False)[0]
    payload = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_detections": 0,
        "total_clusters": 0,
        "cluster_level": "Aman",
        "level_code": 1,
        "detections": []
    }

    if results.boxes is not None and len(results.boxes) > 0:
        boxes = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()

        centroids = []
        total_fire_area = 0

        for box in boxes:
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            area = (box[2] - box[0]) * (box[3] - box[1])
            centroids.append([cx, cy])
            total_fire_area += area

        centroids = np.array(centroids)

        if len(centroids) > 1:
            db = DBSCAN(eps=eps_distance, min_samples=1).fit(centroids)
            cluster_labels = db.labels_
        else:
            cluster_labels = np.array([0])

        num_clusters = len(set(cluster_labels))

        if total_fire_area > 40000:
            level_name = "Level 3"
            level_code = 3
        elif total_fire_area > 10000:
            level_name = "Level 2"
            level_code = 2
        else:
            level_name = "Level 1 (Aman)"
            level_code = 1

        payload["total_detections"] = len(boxes)
        payload["total_clusters"] = num_clusters
        payload["cluster_level"] = level_name
        payload["level_code"] = level_code

        for idx, box in enumerate(boxes):
            xmin, ymin, xmax, ymax = map(int, box)
            c_id = int(cluster_labels[idx])
            cf = float(confs[idx])

            payload["detections"].append({
                "class_name": "fire",
                "confidence": round(cf, 4),
                "cluster_id": c_id,
                "bbox": [xmin, ymin, xmax, ymax]
            })

    return payload, results

# 1. OUTPUT LOG TEKS PER-FRAME
def process_live_cctv_logs(
    cctv_url,
    model_path="/content/drive/MyDrive/Colab Notebooks/content/proyek_cctv/best_v3.pt",
    dashboard_api_url=None,
    conf_threshold=0.45,
    eps_distance=120,
    skip_frames=1
):
    model = YOLO(model_path)
    cap = cv2.VideoCapture(cctv_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Gagal terhubung ke CCTV.")
        return

    print("🟢 Memulai Mode Log Teks Per-Frame...")
    frame_count = 0
    level3_start_time = None

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                cap = cv2.VideoCapture(cctv_url)
                continue

            frame_count += 1
            if frame_count % (skip_frames + 1) != 0:
                continue

            payload, _ = _run_detection(frame, model, conf_threshold, eps_distance)

            # Verification 5 detik berurutan untuk Level 3
            if payload["level_code"] == 3:
                now = time.time()
                if level3_start_time is None:
                    level3_start_time = now
                
                elapsed = now - level3_start_time
                if elapsed > 5.0:
                    payload["cluster_level"] = "Level 3 (Bahaya)"
                else:
                    payload["cluster_level"] = "Level 3"
            else:
                level3_start_time = None

            if payload["level_code"] in [2, 3]:
                print(f"🔥 [{payload['timestamp']}] DETEKSI: {payload['total_detections']} Titik Api | Status: {payload['cluster_level']}")
            else:
                print(f"🟢 [{payload['timestamp']}] Status: Aman (Tidak Ada Api / Level 1)")

            if dashboard_api_url and payload["level_code"] in [2, 3]:
                try:
                    requests.post(dashboard_api_url, json=payload, timeout=0.5)
                except Exception:
                    pass

    except KeyboardInterrupt:
        print("\n🛑 Pengawasan dihentikan.")
    finally:
        cap.release()

# 2. OUTPUT DISPLAY VIDEO STREAMING
def process_live_cctv_video(
    cctv_url,
    model_path="/content/drive/MyDrive/Colab Notebooks/content/proyek_cctv/best_v3.pt",
    dashboard_api_url=None,
    conf_threshold=0.45,
    eps_distance=120,
    skip_frames=1
):
    model = YOLO(model_path)
    cap = cv2.VideoCapture(cctv_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Gagal terhubung ke CCTV.")
        return

    print("🟢 Memulai Live Video Stream (Smooth Mode)...")
    COLOR_MAP = {
        2: (0, 165, 255), # Oranye (Level 2)
        3: (0, 0, 255)    # Merah (Level 3)
    }

    frame_count = 0
    display_handle = None
    level3_start_time = None

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                cap = cv2.VideoCapture(cctv_url)
                continue

            frame_count += 1
            if frame_count % (skip_frames + 1) != 0:
                continue

            payload, _ = _run_detection(frame, model, conf_threshold, eps_distance)

            # Verification 5 detik berurutan untuk Level 3
            if payload["level_code"] == 3:
                now = time.time()
                if level3_start_time is None:
                    level3_start_time = now
                
                elapsed = now - level3_start_time
                if elapsed > 5.0:
                    payload["cluster_level"] = "Level 3 (Bahaya)"
                else:
                    payload["cluster_level"] = "Level 3"
            else:
                level3_start_time = None

            if payload["level_code"] in [2, 3]:
                box_color = COLOR_MAP[payload["level_code"]]
                for det in payload["detections"]:
                    xmin, ymin, xmax, ymax = det["bbox"]
                    c_id = det["cluster_id"]
                    cf = det["confidence"]

                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), box_color, 2)
                    label_text = f"fire | Cluster {c_id} | {cf:.2f}"
                    cv2.putText(frame, label_text, (xmin, max(ymin - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                banner_text = f"STATUS: {payload['cluster_level'].upper()}"
                cv2.rectangle(frame, (10, 10), (450, 50), (0, 0, 0), -1)
                cv2.putText(frame, banner_text, (20, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            else:
                cv2.rectangle(frame, (10, 10), (280, 50), (0, 0, 0), -1)
                cv2.putText(frame, "STATUS: AMAN", (20, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            resized_frame = cv2.resize(frame, (640, 360))
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
            _, buffer = cv2.imencode('.jpg', resized_frame, encode_param)

            image_widget = Image(data=buffer.tobytes())

            if display_handle is None:
                display_handle = display(image_widget, display_id=True)
            else:
                display_handle.update(image_widget)

            if dashboard_api_url and payload["level_code"] in [2, 3]:
                try:
                    requests.post(dashboard_api_url, json=payload, timeout=0.5)
                except Exception:
                    pass

    except KeyboardInterrupt:
        print("\n🛑 Pengawasan dihentikan.")
    finally:
        cap.release()
