FROM runpod/base:0.4.0

WORKDIR /app
COPY worker-requirements.txt ./ 
RUN pip install --no-cache-dir -r worker-requirements.txt
COPY handler.py ./

ENV RUNPOD_HANDLER=handler.handler

# Use the modern, official command to run the worker
CMD ["python", "-m", "runpod.serverless.worker"]