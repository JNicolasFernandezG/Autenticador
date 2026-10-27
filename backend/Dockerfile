FROM python:3.12-slim

# 1. Crear usuario de sistema sin privilegios
RUN useradd -m -r -u 10001 -s /bin/bash appuser

# Directorio de trabajo
WORKDIR /app

# Prevenir archivos .pyc y habilitar salida de logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente y asignar propiedad a appuser
COPY . .
RUN chown -R appuser:appuser /app

# Conmutar a usuario no privilegiado (Non-Root)
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

