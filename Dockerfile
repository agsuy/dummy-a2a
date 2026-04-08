FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src/ src/

RUN pip install --no-cache-dir .

EXPOSE 9000

ENTRYPOINT ["dummy-a2a"]
CMD ["--host", "0.0.0.0", "--port", "9000"]
