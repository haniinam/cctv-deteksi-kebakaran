import os
import json
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from ultralytics import YOLO

def process_fire_telemetry(
    video_input_path,
    model_path="/content/drive/MyDrive/Colab Notebooks/content/proyek_cctv/best_v3.pt",
    output_dir="/content/drive/MyDrive/Colab Notebooks/content/proyek_cctv/output",
    conf_threshold=0.15,
    eps_distance=120
):
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.splitext(os.path.basename(video_input_path))[0]
    video_output_path = os.path.join(output_dir, f"{filename}_telemetry2.mp4")
    json_output_path = os.path.join(output_dir, f"{filename}_telemetry2.json")

    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_input_path)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = int(cap.get(cv2.CAP_PROP_FPS)) or 30

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(video_output_path, fourcc, fps, (width, height))

    COLOR_MAP = {
        2: (0, 165, 255),     # Oranye
        3: (0, 0, 255)        # Merah
    }

    json_output_data = []
    frame_idx = 0
    level3_start_sec = None

    print(f"⏳ Memproses video '{filename}' dan membuat telemetri...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        current_sec = frame_idx / fps
        results = model.predict(frame, conf=conf_threshold, verbose=False)[0]

        frame_info = {
            "frame": frame_idx,
            "total_detections": 0,
            "total_clusters": 0,
            "cluster_level": "Aman",
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
                level_code = 3
                if level3_start_sec is None:
                    level3_start_sec = current_sec
                
                if (current_sec - level3_start_sec) > 5.0:
                    level_name = "Level 3 (Bahaya)"
                else:
                    level_name = "Level 3"
            elif total_fire_area > 10000:
                level_code = 2
                level_name = "Level 2"
                level3_start_sec = None
            else:
                level_code = 1
                level_name = "Level 1 (Aman)"
                level3_start_sec = None

            frame_info["total_detections"] = len(boxes)
            frame_info["total_clusters"] = num_clusters
            frame_info["cluster_level"] = level_name

            for idx, box in enumerate(boxes):
                xmin, ymin, xmax, ymax = map(int, box)
                c_id = int(cluster_labels[idx])
                cf = float(confs[idx])

                frame_info["detections"].append({
                    "class_name": "fire",
                    "confidence": round(cf, 4),
                    "cluster_id": c_id,
                    "bbox": [xmin, ymin, xmax, ymax]
                })

            if level_code in [2, 3]:
                box_color = COLOR_MAP[level_code]
                for det in frame_info["detections"]:
                    xmin, ymin, xmax, ymax = det["bbox"]
                    c_id = det["cluster_id"]
                    cf = det["confidence"]
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), box_color, 2)
                    label_text = f"fire | Cluster {c_id} | {cf:.2f}"
                    cv2.putText(frame, label_text, (xmin, max(ymin - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                banner_text = f"STATUS: {level_name.upper()}"
                cv2.rectangle(frame, (10, 10), (450, 50), (0, 0, 0), -1)
                cv2.putText(frame, banner_text, (20, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
            else:
                cv2.rectangle(frame, (10, 10), (280, 50), (0, 0, 0), -1)
                cv2.putText(frame, "STATUS: AMAN", (20, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            level3_start_sec = None
            cv2.rectangle(frame, (10, 10), (280, 50), (0, 0, 0), -1)
            cv2.putText(frame, "STATUS: AMAN", (20, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        json_output_data.append(frame_info)
        out_video.write(frame)

    cap.release()
    out_video.release()

    with open(json_output_path, "w") as f:
        json.dump(json_output_data, f, indent=4)

    print(f"🎉 Selesai!")
    print(f"🎥 Video tersimpan di: {video_output_path}")
    print(f"📄 JSON tersimpan di: {json_output_path}")
    return video_output_path, json_output_path
