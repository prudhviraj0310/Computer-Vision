FROM python:3.11-slim

# Install system dependencies for OpenCV, EasyOCR, and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifest and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLO weights and EasyOCR English models into the container image cache
# This prevents runtime download delays on startup
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"
RUN python -c "import easyocr; easyocr.Reader(['en'])"

# Copy application source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
