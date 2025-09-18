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

# Optional: Install OmniGibson + BDDL into the Isaac Sim Python env
# Enable by building with: --build-arg INSTALL_OG=true
ARG INSTALL_OG=false
ARG OG_BRANCH=v3.7.1
RUN if [ "$INSTALL_OG" = "true" ]; then \
        echo "Installing OmniGibson (attempt PyPI, else source from BEHAVIOR-1K $OG_BRANCH)" && \
        set -ex; \
        /isaac-sim/python.sh -m pip install --upgrade pip; \
        (/isaac-sim/python.sh -m pip install bddl omnigibson && echo "Installed omnigibson from PyPI") || \
        (echo "Falling back to source install from BEHAVIOR-1K" && \
            git clone -b "$OG_BRANCH" --depth 1 https://github.com/StanfordVL/BEHAVIOR-1K.git /opt/BEHAVIOR-1K && \
            /isaac-sim/python.sh -m pip install -e /opt/BEHAVIOR-1K/bddl || true && \
            /isaac-sim/python.sh -m pip install -e /opt/BEHAVIOR-1K/omnigibson); \
    else \
        echo "Skipping OmniGibson install (INSTALL_OG=false)."; \
    fi

# Default command (can be overridden)
CMD ["bash"]