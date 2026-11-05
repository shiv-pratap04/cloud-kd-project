FROM python:3.11-slim
RUN pip install --no-cache-dir boto3==1.35.20
WORKDIR /app
COPY worker/*.py /app/
COPY prompts/teacher_prompt.txt /app/teacher_prompt.txt
CMD ["python", "worker.py"]
