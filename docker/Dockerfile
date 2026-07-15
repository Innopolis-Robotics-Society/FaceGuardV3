FROM python:3.10-slim
WORKDIR /app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        libgl1 \
        libxcb1 \
        libglib2.0-0 \
        libgomp1 \
        tzdata \
        build-essential \
        python3-dev \
        swig \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

# InsightFace's base metadata requires the GUI OpenCV distribution. Install
# its explicitly pinned dependencies first, then install the pure-Python wheel
# without dependencies to keep one headless cv2 implementation in the image.
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        --no-deps insightface==1.0.1

COPY backend/ ./backend/

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]