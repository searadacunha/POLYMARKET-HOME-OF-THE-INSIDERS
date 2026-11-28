# Serves a folder of pages built by `python3 -m phi_forensics.viz build`. Build from the repository root:
#   docker build -f deploy/viewer/Dockerfile -t phi-forensics-viewer .
# The server reads files only; it needs no secret and opens no outbound connection.
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
RUN useradd --uid 10001 --user-group --no-create-home --shell /usr/sbin/nologin viewer
COPY monitoring/__init__.py /app/monitoring/__init__.py
COPY monitoring/phi_monitor/ /app/monitoring/phi_monitor/
COPY phi_forensics/ /app/phi_forensics/
COPY docs/examples/*.html /srv/pages/

USER 10001:10001
WORKDIR /app
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD ["python3", "-c", "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:8080/', timeout=4).status != 200)"]
CMD ["python3", "-m", "phi_forensics.viz", "serve", "/srv/pages", "--host", "0.0.0.0", "--port", "8080"]
