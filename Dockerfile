FROM python:3.10.8

WORKDIR /app

# System dependencies needed for OpenCV / OCR / ML
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]