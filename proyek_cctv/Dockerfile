# 1. Pilih sistem operasi dasar yang sudah terinstall Python 3.10
FROM python:3.10-slim

# 2. Install library pendukung sistem Linux yang dibutuhkan oleh OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libffmpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Tentukan folder kerja di dalam komputer virtual Docker
WORKDIR /app

# 4. Salin daftar library (requirements.txt) ke dalam folder kerja Docker
COPY requirements.txt .

# 5. Install semua library Python (ultralytics, opencv, dll.)
RUN pip install --no-cache-dir -r requirements.txt

# 6. Salin seluruh file proyek Anda ke dalam Docker
COPY . .

# 7. Perintah yang akan langsung dijalankan saat Docker dinyalakan
CMD ["python", "fire_pipeline.py"]