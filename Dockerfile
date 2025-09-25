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
    ca-certificates git wget curl unzip ffmpeg build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Copy project files
COPY . /workspace

# Install Python dependencies into Isaac Sim's Python environment
RUN /isaac-sim/python.sh -m pip install --upgrade pip && \
    /isaac-sim/python.sh -m pip install -r requirements.txt

# OmniGibson install (BEHAVIOR-1K + OmniGibson)
RUN /isaac-sim/python.sh -m pip install --upgrade pip && \
    git clone --depth 1 https://github.com/StanfordVL/BEHAVIOR-1K.git /opt/BEHAVIOR-1K && \
    cd /opt/BEHAVIOR-1K/bddl && \
    /isaac-sim/python.sh -m pip install -e . && \
    cd /opt/BEHAVIOR-1K/OmniGibson && \
    /isaac-sim/python.sh -m pip install -e .

# Optional dataset download
ARG DOWNLOAD_DATASETS=false
RUN if [ "$DOWNLOAD_DATASETS" = "true" ]; then \
        echo "Downloading OmniGibson datasets..." && \
        cd /opt/BEHAVIOR-1K && \
        /isaac-sim/python.sh -c "from omnigibson.utils.asset_utils import download_omnigibson_robot_assets; download_omnigibson_robot_assets()" && \
        /isaac-sim/python.sh -c "from omnigibson.utils.asset_utils import download_behavior_1k_assets; download_behavior_1k_assets(accept_license=True)" && \
        /isaac-sim/python.sh -c "from omnigibson.utils.asset_utils import download_2025_challenge_task_instances; download_2025_challenge_task_instances()"; \
    else \
        echo "Skipping dataset download (DOWNLOAD_DATASETS=false)."; \
    fi

ENV OMNIGIBSON_HEADLESS=1
ENV HEADLESS=1
ENV DISPLAY=

# Default command (can be overridden)
CMD ["bash"]