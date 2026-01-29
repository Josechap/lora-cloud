FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Python deps
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install kohya_ss
RUN git clone https://github.com/kohya-ss/sd-scripts.git /workspace/sd-scripts \
    && cd /workspace/sd-scripts \
    && pip3 install --no-cache-dir -r requirements.txt

# Install captioning models
RUN pip3 install --no-cache-dir \
    transformers[torch] \
    open-clip-torch

# Copy scripts and configs
COPY scripts/ /workspace/scripts/
COPY configs/ /workspace/configs/
COPY startup.sh /workspace/

RUN chmod +x /workspace/startup.sh

EXPOSE 22

CMD ["/workspace/startup.sh"]
