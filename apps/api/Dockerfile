FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /workspace

COPY apps/api/requirements.txt /workspace/requirements.txt
RUN python -m pip install --no-cache-dir -r /workspace/requirements.txt

# Copy app source (only contents, not folder)
COPY apps/api/ /workspace/apps/api/
COPY packages/shared/ /workspace/packages/shared/

# Set working directory to app root
WORKDIR /workspace/apps/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
