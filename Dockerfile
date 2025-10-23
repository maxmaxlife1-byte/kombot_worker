FROM python:3.9-slim

WORKDIR /app
COPY worker-requirements.txt ./ 
RUN pip install --no-cache-dir -r worker-requirements.txt
COPY handler.py ./

ENV RUNPOD_HANDLER=handler.handler

CMD ["python", "-m", "runpod.serverless.worker"]