FROM python:3.12-slim

# Install SSH client and ping utility (for connectivity checks)
RUN apt-get update && apt-get install -y openssh-client iputils-ping && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY 8311-ha-bridge.py .

# Run the application
CMD ["python3", "-u", "8311-ha-bridge.py"]
