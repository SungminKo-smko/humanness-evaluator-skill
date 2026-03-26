# =============================================================================
# Humanness Evaluator — MCP Server Docker Image
#
# Build:  docker build -t humanness-evaluator .
# Run:    docker run -p 8000:8000 humanness-evaluator
# =============================================================================

FROM continuumio/miniconda3:24.1.2-0

WORKDIR /app

# Install system dependencies (HMMER needs these)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install HMMER and abnumber via conda (must be before pip installs)
RUN conda install -y -c bioconda -c conda-forge \
    python=3.9 \
    abnumber \
    hmmer \
    && conda clean -afy

# Copy dependency files first (layer caching)
COPY environment.yml setup.py ./
COPY biophi/  ./biophi/

# Install biophi package and all pip dependencies
RUN pip install --no-cache-dir -e ".[viz]"

# Install MCP server dependencies
RUN pip install --no-cache-dir \
    "mcp>=1.0.0" \
    "uvicorn[standard]>=0.30.0" \
    "starlette>=0.40.0"

# Copy remaining skill files
COPY agent_api.py patches/ ./patches/
COPY agent_api.py ./
COPY mcp_server.py ./
COPY scripts/  ./scripts/
COPY references/ ./references/

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

CMD ["python", "mcp_server.py"]
