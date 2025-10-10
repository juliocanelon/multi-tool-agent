# docker/gemini-cli.Dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Herramientas del “CLI”
COPY docker/tools /app/tools

# Default: queda esperando si lo corres sin comando
CMD ["bash", "-lc", "echo 'CLI placeholder listo' && tail -f /dev/null"]
