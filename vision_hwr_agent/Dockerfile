# 1. Start from an official Python 3.10 image
FROM python:3.10-slim

# 2. Set up the working directory
WORKDIR /app

# 3. Copy and install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the agent's code into the container
COPY . .

# 5. Command to run the agent
CMD ["python", "-u", "agent.py"]