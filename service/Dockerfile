FROM python:3.11-slim
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1
WORKDIR /app
# CPU-only torch wheel (no CUDA libraries) keeps the image well under 2 GB
RUN pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
COPY service/requirements.txt .
RUN pip install -r requirements.txt
COPY service/app.py service/validation.py ./
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
