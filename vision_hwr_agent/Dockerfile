# /composable-orchestrator/vision_hwr_agent/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Install Tesseract OCR engine
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This command will start the listener script
CMD ["python", "agent.py"]