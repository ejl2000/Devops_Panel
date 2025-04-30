# Use Debian-based slim Python image
FROM python:3.12-slim

# Install system dependencies, including LLVM 14
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    cargo \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    bash \
    curl \
    llvm-14 \
    clang \
    && rm -rf /var/lib/apt/lists/*

# Create a symlink for llvm-config
RUN ln -s /usr/bin/llvm-config-14 /usr/local/bin/llvm-config

# Install Poetry
ENV POETRY_VERSION=1.6.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Configure Poetry
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

WORKDIR /app

# Copy dependency definitions
COPY poetry.lock pyproject.toml /app/

# Install dependencies using the updated Poetry command
RUN poetry install --only main --no-interaction --no-ansi

# Copy the entire project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=InternalDevOpsPanel.settings \
    LLVM_CONFIG=/usr/local/bin/llvm-config

# Expose port 8000
EXPOSE 8000

# Start the application using Gunicorn
#CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]