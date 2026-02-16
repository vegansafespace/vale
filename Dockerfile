FROM ghcr.io/astral-sh/uv:python3.9-alpine

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-cache

COPY src/ ./src

CMD ["uv", "run", "python", "-m", "src.main"]
