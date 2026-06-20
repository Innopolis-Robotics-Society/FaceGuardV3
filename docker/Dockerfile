FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    streamlit \
    psycopg2-binary \
    opencv-python \
    insightface \
    onnxruntime \
    numpy \
    pandas

COPY backend/ ./backend/

EXPOSE 8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "backend/pages/page_authentication.py"]
