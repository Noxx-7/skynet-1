FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 llmuser
USER llmuser
WORKDIR /home/llmuser

# Copy requirements and install Python packages
COPY --chown=llmuser:llmuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create workspace directory
RUN mkdir -p /home/llmuser/workspace
WORKDIR /home/llmuser/workspace

# Common ML/LLM libraries
RUN pip install --no-cache-dir \
    transformers>=4.35.0 \
    torch>=2.0.0 \
    numpy>=1.24.0 \
    pandas>=2.0.0 \
    scikit-learn>=1.3.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0

# Set environment variables
ENV PYTHONPATH=/home/llmuser/workspace
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 8000), timeout=10)"

CMD ["python", "-m", "uvicorn", "sandbox_app:app", "--host", "0.0.0.0", "--port", "8000"]