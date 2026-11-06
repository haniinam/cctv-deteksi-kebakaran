# ==================================
# CCTV FIRE DETECTION WORKER
#   python worker.py            -> headless (server)
#   python worker.py --show     -> tampilkan jendela (ESC untuk keluar)
# ==================================

import argparse
import json
import signal
import time

import cv2

from config import CAMERAS_FILE, SAVE_INTERVAL
import overlay
from fire import FireDetector
from output import OutputManager
from video_stream import VideoStream

WINDOW_NAME = "CCTV FIRE DETECTION"
LEVEL_COLORS = {1: (0, 200, 0), 2: (0, 165, 255), 3: (0, 0, 255)}  # BGR
# di dashboard gabungan api selalu merah muda, supaya tidak tertukar dengan warna
# kendaraan (hijau/biru/kuning/oranye) dan kecelakaan (merah/ungu); level tampil di status
DASHBOARD_FIRE_COLOR = (147, 20, 255)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--show", action="store_true", help="tampilkan jendela video")
    p.add_argument("--camera", type=int, default=0, help="index kamera di cameras.json")
    p.add_argument("--source", help="override sumber video (mis. test-fire.mp4)")
    p.add_argument("--loop", action="store_true", help="ulangi video file saat selesai")
    p.add_argument("--duration", type=float, help="berhenti otomatis setelah sekian detik")
    return p.parse_args()


def draw(frame, result, camera_name):
    color = LEVEL_COLORS[result["level_code"]]
    for d in result["detections"]:
        x1, y1, x2, y2 = d["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"fire | Cluster {d['cluster_id']} | {d['confidence']:.2f}",
                    (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(frame, f"Camera: {camera_name}", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, f"Status: {result['cluster_level'].upper()}", (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3, cv2.LINE_AA)


def main():
    args = parse_args()

    with open(CAMERAS_FILE, "r", encoding="utf-8") as f:
        camera = json.load(f)[args.camera]
    source = args.source or camera["source"]

    print("==============================")
    print(" CCTV FIRE SERVER START ")
    print("==============================")
    print("Camera :", camera["name"])
    print("Source :", source)

    stream = VideoStream(source, loop=args.loop)
    detector = FireDetector()
    output = OutputManager(camera)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    if args.show:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    last_save = time.time()
    worst = None   # hasil terburuk selama interval simpan (supaya api singkat tidak terlewat)
    start = time.time()
    while running and not stream.ended:
        if args.duration and time.time() - start >= args.duration:
            break
        frame = stream.read()
        if frame is None:
            continue

        result = detector.detect(frame, stream.time)
        overlay.publish(
            "fire", frame.shape, result["cluster_level"],
            f"{result['total_detections']} titik api, {result['fire_area']} px", result["level_code"] - 1,
            [(tuple(d["bbox"]), f"FIRE {d['confidence']:.2f}", DASHBOARD_FIRE_COLOR)
             for d in result["detections"]],
        )
        rank = (result["level_code"], result["fire_area"])
        if worst is None or rank > (worst["level_code"], worst["fire_area"]):
            worst = result

        now = time.time()
        if now - last_save >= SAVE_INTERVAL:
            data = output.generate(worst)
            output.save_json(data)
            output.display(data)
            worst, last_save = None, now

        if args.show:
            draw(frame, result, camera["name"])
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) == 27:
                break

    if worst is not None:
        data = output.generate(worst)
        output.save_json(data)
        output.display(data)
    stream.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
