FROM python:3.10-slim-buster

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install synthetic data generation package from a stable path
COPY synthetic_data_generation /src/synthetic_data_generation
RUN pip install -e /src/synthetic_data_generation

# Copy backend code
COPY backend /app

# Expose port
EXPOSE 5000

# Set environment variable
ENV PYTHONPATH=/app:/src

# Start the application
CMD ["python3", "run.py"]
