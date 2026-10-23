FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir hermes-agent aiohttp websockets

WORKDIR /app
COPY . /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 10000
CMD ["/app/entrypoint.sh"]
