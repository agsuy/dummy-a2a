FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src/ src/

RUN uv sync --locked --no-dev --no-editable

EXPOSE 9000

ENTRYPOINT ["uv", "run", "dummy-a2a"]
CMD ["--host", "0.0.0.0", "--port", "9000"]
