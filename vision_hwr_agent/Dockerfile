# /composable-orchestrator/vision_hwr_agent/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# We NO LONGER need tesseract or opencv dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This command will start the listener script
CMD ["python", "agent.py"]