FROM python:3.10-slim

WORKDIR /app

# Install dependencies required for some python packages and Oracle instant client if needed
RUN apt-get update && apt-get install -y \
    gcc \
    libaio1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip and install requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose ports for FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501
