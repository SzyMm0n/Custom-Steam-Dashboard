FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone https://github.com/SzyMm0n/Custom-Steam-Dashboard.git .

RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["venv/bin/uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]