FROM python:3.10.20-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        libglib2.0-0 \
        libgomp1 \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

# InsightFace's base metadata requires the GUI OpenCV distribution. Install
# its explicitly pinned dependencies first, then install the pure-Python wheel
# without dependencies to keep one headless cv2 implementation in the image.
RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        --no-deps insightface==1.0.1

COPY backend/ ./backend/

WORKDIR /app/backend
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
