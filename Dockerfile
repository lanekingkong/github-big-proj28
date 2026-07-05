# UniSkill - Universal Agent Capability Mesh
# Multi-stage Docker build for production deployment

FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="UniSkill"
LABEL org.opencontainers.image.description="Universal Agent Capability Mesh - Enterprise MCP Server, Context Compression, Security Scanning, A2A Routing"
LABEL org.opencontainers.image.source="https://github.com/lanekingkong/uniskill"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash uniskill
WORKDIR /app

# ---- Build Stage ----
FROM base AS builder

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime Stage ----
FROM base AS runtime

# Copy Python packages from builder
COPY --from=builder /root/.local /home/uniskill/.local

# Copy application
COPY --chown=uniskill:uniskill src/ /app/src/
COPY --chown=uniskill:uniskill pyproject.toml README.md /app/

# Set environment
ENV PATH="/home/uniskill/.local/bin:${PATH}"
ENV PYTHONPATH="/app/src:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1

# MCP server port
EXPOSE 8787
# A2A router port
EXPOSE 8788
# API port
EXPOSE 8000

# Switch to non-root user
USER uniskill

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from uniskill.core import UniSkillEngine; e = UniSkillEngine(); print(e.health_check()['status'])"

ENTRYPOINT ["python", "-m", "uniskill.cli"]
CMD ["info"]
