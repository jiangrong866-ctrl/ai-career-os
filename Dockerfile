FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY . /app

HEALTHCHECK --interval=5m --timeout=30s --retries=3 CMD ["python", "scripts/healthcheck.py"]

CMD ["python", "scripts/daemon_loop.py"]
