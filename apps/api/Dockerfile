FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY apps/api/requirements.txt /workspace/apps/api/requirements.txt
RUN python -m pip install --no-cache-dir -r /workspace/apps/api/requirements.txt

COPY apps/api /workspace/apps/api
COPY packages/shared /workspace/packages/shared

WORKDIR /workspace/apps/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
