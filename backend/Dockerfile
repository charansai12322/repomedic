# Multi-stage production Dockerfile for RepoMedic Backend
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt semgrep

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN groupadd -g 10001 repomedic && \
    useradd -u 10001 -g repomedic -s /bin/bash -m repomedic

# Copy installed wheels from builder
COPY --from=builder /root/.local /home/repomedic/.local
ENV PATH=/home/repomedic/.local/bin:$PATH
ENV PYTHONPATH=/app

# Copy backend application code
COPY repomedic/ /app/repomedic/
COPY main.py /app/main.py

# Set proper ownership
RUN chown -R repomedic:repomedic /app /home/repomedic

USER repomedic

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "repomedic.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
