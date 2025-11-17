FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the purge script
COPY purge.py .

# Make script executable
RUN chmod +x purge.py

# Create data directory (will be mounted as volume)
RUN mkdir -p /data

# Run the purge script
CMD ["python", "-u", "purge.py"]
