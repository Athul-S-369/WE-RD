FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY packages ./packages
COPY apps/api ./apps/api
COPY workers ./workers
COPY database ./database

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "weird.api:app", "--host", "0.0.0.0", "--port", "8000"]
