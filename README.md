# 🎥 Real-Time Fire Detection & Clustering Telemetry Pipeline

Sistem pemantauan dan deteksi dini kebakaran berbasis **YOLOv8** dan **DBSCAN Clustering**. Sistem ini menganalisis titik api dari *feed* CCTV *live* maupun berkas video, mengelompokkan persebaran titik api, serta mengklasifikasikan tingkat bahaya kebakaran secara *real-time*.

---

## 🚀 Fitur Utama

- **Deteksi Api Presisi Tinggi**: Menggunakan model YOLOv8 yang dioptimalkan untuk mendeteksi titik/area api.
- **Klasterisasi Spasial (DBSCAN)**: Mengelompokkan titik-titik api yang berdekatan untuk menghitung estimasi cakupan area kebakaran.
- **Hierarki Tingkat Bahaya (Multi-Level Alert)**:
  - **Aman (Level 1)**: Tidak ada api terdeteksi atau area api < 10.000 px.
  - **Level 2 (Sedang)**: Area api berkisar antara 10.000 – 40.000 px.
  - **Level 3**: Area api > 40.000 px.
  - **Level 3 (Bahaya)**: Terdeteksi status Level 3 secara **berurutan selama lebih dari 5 detik** untuk mencegah *false positive*.
- **Dukungan CCTV Live & Video Offline**:
  - `fire_pipeline_live.py`: Untuk *stream* CCTV (RTSP/HTTP) dengan visualisasi lancar & pengiriman log telemetri ke API Dashboard.
  - `fire_pipeline.py`: Untuk pemrosesan berkas `.mp4` offline yang menghasilkan video hasil analisis dan berkas `telemetry.json`.
- **Dukungan Docker Container**: Aplikasi disiapkan agar dapat di-deploy dengan mudah di lingkungan Linux/Server.

---

## 🛠️ Struktur Proyek

```text
.
├── Dockerfile                  # Konfigurasi containerization
├── requirements.txt            # Daftar dependensi Python
├── fire_pipeline.py            # Script pemrosesan video offline & JSON telemetry
├── fire_pipeline_live.py       # Script pengawasan live CCTV & integrasi API (Colab)
├── worker.py                   # Mode server: live CCTV headless, simpan tiap 10 detik
├── fire.py                     # Deteksi + DBSCAN + level bahaya (logika sama dengan fire_pipeline_live.py)
├── config.py                   # Semua pengaturan (bisa diganti lewat environment variable)
├── video_stream.py             # Pembaca stream: selalu frame terbaru, sambung ulang otomatis
├── output.py / db.py / api.py  # JSON, log harian, database PostgreSQL, REST API
├── overlay.py                  # Kotak api terbaru untuk dashboard gabungan
├── docker-compose.yml          # worker + api
├── data/cameras.json           # Daftar kamera (id, nama, lokasi, sumber stream)
├── models/fire_openvino_model/ # best_v3.pt diekspor ke OpenVINO (640 px)
└── README.md                   # Dokumen panduan penggunaan
```

---

## 📦 Unduh Model Weights (`.pt`)

Karena ukuran berkas bobot model cukup besar, berkas `best_v3.pt` dapat diunduh melalui halaman **Releases** repositori ini:

- 🔗 **[Unduh Model Weights (best_v3.pt)](https://github.com/haniinam/cctv-deteksi-kebakaran/releases)**

Setelah diunduh, simpan berkas `best_v3.pt` di direktori utama proyek.

---

## 💻 Panduan Penggunaan

### 1. Menjalankan via Python (Native)

**Prasyarat:**
- Python 3.10+

**Instalasi Dependensi:**
```bash
pip install -r requirements.txt
```

**Mode Live CCTV:**
```python
from fire_pipeline_live import process_live_cctv_logs, process_live_cctv_video

# Untuk log teks per-frame:
process_live_cctv_logs(cctv_url="URL_RTSP_ATAU_STREAM_CCTV", model_path="best_v3.pt")

# Untuk streaming video visualisasi:
process_live_cctv_video(cctv_url="URL_RTSP_ATAU_STREAM_CCTV", model_path="best_v3.pt")
```

**Mode Video Offline:**
```python
from fire_pipeline import process_fire_telemetry

process_fire_telemetry(video_input_path="input_video.mp4", model_path="best_v3.pt")
```

---

### 2. Mode Server (OpenVINO, tanpa Colab)

`worker.py` menjalankan deteksi pada stream di `data/cameras.json` memakai model OpenVINO
(`models/fire_openvino_model`, hasil ekspor `best_v3.pt`, ±0,7 detik/frame di CPU vs ±1,5 detik/frame PyTorch).
Logika deteksi sama dengan `fire_pipeline_live.py`: confidence 0,45, DBSCAN eps 120,
Level 2 > 10.000 px, Level 3 > 40.000 px, Level 3 lebih dari 5 detik = "Level 3 (Bahaya)".

```bash
pip install -r requirements.txt
python worker.py                          # headless, status tiap 10 detik
python worker.py --show                   # dengan jendela video (ESC untuk keluar)
python worker.py --source test-fire4.mp4  # uji dengan file video
uvicorn api:app --port 8000               # API: /health, /fire/latest, /fire/history
```

Setiap 10 detik (status terburuk dalam 10 detik itu, termasuk "Aman"):
`logs/fire_data.json`, `logs/fire_YYYYMMDD.jsonl`, dan tabel `fire_snapshots` jika env `DATABASE_URL` diisi.
Waktu memakai WIB dengan zona waktu (`+07:00`) dan setiap data membawa `camera_id`.

---

### 3. Menjalankan via Docker Container

```bash
docker compose up -d --build      # worker + API (http://localhost:8000/fire/latest)
docker compose logs -f worker
docker compose down
```

`data/`, `models/`, dan `logs/` di-mount dari host, jadi kamera dan model bisa diganti tanpa build ulang.
Image memakai Python 3.12 (Python 3.10 tidak lagi didukung PyTorch terbaru) dan versi library dikunci di `requirements.txt`.

---

## 📡 Integrasi Dashboard API

Sistem dapat mengirimkan payload telemetri berupa JSON ke endpoint API Dashboard secara otomatis saat level bahaya terdeteksi di **Level 2** atau **Level 3**.

Format Payload JSON:
```json
{
  "timestamp": "2026-03-09 14:30:00",
  "total_detections": 4,
  "total_clusters": 2,
  "cluster_level": "Level 3 (Bahaya)",
  "level_code": 3,
  "detections": [
    {
      "class_name": "fire",
      "confidence": 0.8921,
      "cluster_id": 0,
      "bbox": [120, 85, 310, 240]
    }
  ]
}
```