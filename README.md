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
├── fire_pipeline_live.py       # Script pengawasan live CCTV & integrasi API
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

### 2. Menjalankan via Docker Container

**Build Docker Image:**
```bash
docker build -t fire-detection-app .
```

**Jalankan Container:**
```bash
docker run --rm fire-detection-app
```

**Jalankan dengan Volume Mount (Akses Berkas Lokal dari Dalam Container):**
```bash
docker run --rm -v ${PWD}:/app fire-detection-app python fire_pipeline.py
```

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