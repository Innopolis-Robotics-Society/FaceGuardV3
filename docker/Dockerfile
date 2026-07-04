FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    build-essential \
    python3-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir numpy pandas psycopg2-binary
RUN pip install --no-cache-dir opencv-python onnxruntime
RUN pip install --no-cache-dir streamlit streamlit-webrtc pytest
RUN pip install --no-cache-dir gpiozero RPi.GPIO
RUN pip install --no-cache-dir insightface

VOLUME ["/app/backend", "/app/tests"]

EXPOSE 8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV PYTHONPATH=/app

CMD ["bash"]
