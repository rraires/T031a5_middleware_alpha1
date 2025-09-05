# Multi-stage build for t031a5_middleware
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libasound2-dev \
    portaudio19-dev \
    libopencv-dev \
    python3-opencv \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy isort pre-commit

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e ".[dev]"

# Expose ports
EXPOSE 8000 8001 9090

# Default command for development
CMD ["python", "main.py", "--config", "config.json"]

# Production stage
FROM base as production

# Create non-root user
RUN groupadd -r middleware && useradd -r -g middleware middleware

# Copy source code
COPY --chown=middleware:middleware . .

# Install package
RUN pip install .

# Create necessary directories
RUN mkdir -p logs data/recordings && \
    chown -R middleware:middleware logs data

# Switch to non-root user
USER middleware

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose ports
EXPOSE 8000 8001 9090

# Default command
CMD ["python", "main.py", "--config", "config.json"]

# Testing stage
FROM development as testing

# Run tests
RUN python -m pytest tests/ -v --cov=t031a5_middleware --cov-report=html

# Linting stage
FROM development as linting

# Run code quality checks
RUN black --check . && \
    flake8 . && \
    mypy . && \
    isort --check-only .

# Final production image
FROM production as final

# Add labels
LABEL maintainer="Unitree Robotics <support@unitree.com>" \
      version="1.0.0" \
      description="Advanced middleware system for Unitree quadruped robots" \
      org.opencontainers.image.source="https://github.com/unitree/t031a5_middleware" \
      org.opencontainers.image.documentation="https://docs.unitree.com/middleware" \
      org.opencontainers.image.licenses="MIT"

# Add build info
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$VCS_REF