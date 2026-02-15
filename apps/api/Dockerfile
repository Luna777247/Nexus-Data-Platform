FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY apps/api/requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy app source (chỉ nội dung, không folder)
COPY . .

# Copy toàn bộ project vào /workspace (build context là thư mục gốc)
COPY . /workspace

# Set working directory to project root (cha của apps)
WORKDIR /workspace

# Ensure PYTHONPATH includes /workspace for absolute imports
ENV PYTHONPATH="/workspace"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
