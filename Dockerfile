# Isaac Sim 4.5.0 base image from NVIDIA NGC
FROM nvcr.io/nvidia/isaac-sim:4.5.0

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Optional CUDA build flags for any torch/cpp extensions built at image time
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9" \
    FORCE_CUDA=1

# Install minimal extra tools (Isaac Sim image already has graphics libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git wget curl unzip ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Copy project files
COPY . /workspace

# Install Python dependencies into Isaac Sim's Python environment
RUN /isaac-sim/python.sh -m pip install --upgrade pip && \
    /isaac-sim/python.sh -m pip install -r requirements.txt

# OmniGibson install (BEHAVIOR-1K + OmniGibson)
ARG INSTALL_OG=false
ARG OG_BRANCH=main
RUN /isaac-sim/python.sh -m pip install --upgrade pip; \
    git clone --depth 1 --branch "$OG_BRANCH" https://github.com/StanfordVL/BEHAVIOR-1K.git /opt/BEHAVIOR-1K && \
    cd /opt/BEHAVIOR-1K/bddl && \
    /isaac-sim/python.sh -m pip install -e . && \
    cd /opt/BEHAVIOR-1K/OmniGibson && \
    /isaac-sim/python.sh -m pip install -e .

# Default command (can be overridden)
CMD ["bash"]