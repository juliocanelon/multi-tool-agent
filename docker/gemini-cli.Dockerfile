FROM python:3.11-slim
WORKDIR /app
# Instala aquí el CLI real cuando lo definamos (gemini/uv/whatever)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY data /app/data
COPY workdir /app/workdir
CMD ["bash", "-lc", "echo 'CLI placeholder listo' && tail -f /dev/null"]
