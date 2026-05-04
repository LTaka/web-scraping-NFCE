FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    scrot \
    xclip \
    xsel \
    tesseract-ocr \
    tesseract-ocr-por \
    libx11-6 \
    libxtst6 \
    libxrender1 \
    libxrandr2 \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "processar_csv.py", "exemplo_entrada.csv", "--saida", "resultado.csv", "--modo", "executar"]
