FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI

WORKDIR /workspace/ComfyUI
RUN pip3 install --no-cache-dir -r requirements.txt

# Install ComfyUI Manager
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-Manager

# Install essential custom nodes
RUN git clone https://github.com/rgthree/rgthree-comfy.git \
    /workspace/ComfyUI/custom_nodes/rgthree-comfy \
    && git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite \
    && git clone https://github.com/kijai/ComfyUI-Florence2.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-Florence2

# GCS sync
RUN pip3 install --no-cache-dir google-cloud-storage

COPY startup.sh /workspace/
COPY scripts/ /workspace/scripts/
COPY workflows/ /workspace/ComfyUI/user/default/workflows/

RUN chmod +x /workspace/startup.sh

EXPOSE 8188

CMD ["/workspace/startup.sh"]
