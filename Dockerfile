# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Set environment variables for non-interactive installs
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    ca-certificates git wget curl unzip \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
    libx11-6 libxrandr2 libxi6 libxtst6 libnss3 libxkbcommon0 \
    libdrm2 libasound2 libxfixes3 libxxf86vm1 \
    mesa-utils \
    xvfb x11-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Copy project files
COPY . /workspace

# Install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt

# Optional: Install OmniGibson from BEHAVIOR-1K (route B)
# This is heavy and may require NVIDIA EULA acceptance and large downloads.
# Enable by building with: --build-arg INSTALL_OG=true
ARG INSTALL_OG=false
ARG OG_BRANCH=v3.7.1
ARG OG_CUDA_VERSION=12.2
RUN if [ "$INSTALL_OG" = "true" ]; then \
      echo "Installing OmniGibson from BEHAVIOR-1K (branch: $OG_BRANCH)" && \
      git clone -b "$OG_BRANCH" --depth 1 https://github.com/StanfordVL/BEHAVIOR-1K.git /opt/BEHAVIOR-1K && \
      cd /opt/BEHAVIOR-1K && chmod +x setup.sh && \
      ./setup.sh --omnigibson --bddl --primitives --eval \
                 --confirm-no-conda --cuda-version "$OG_CUDA_VERSION" \
                 --accept-nvidia-eula --accept-dataset-tos || \
      (echo "OmniGibson setup script failed. Check logs and ensure network/EULA." && exit 1); \
    else \
      echo "Skipping OmniGibson install (INSTALL_OG=false)."; \
    fi

# Default command (can be overridden)
CMD ["bash"]