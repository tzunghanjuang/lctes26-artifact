FROM ubuntu:latest

ENV SBT_OPTS="-Xms1G -Xmx6G -XX:+UseG1GC -XX:MaxMetaspaceSize=1G"
ENV JAVA_OPTS="-Xms1G -Xmx6G"

ARG DEBIAN_FRONTEND=noninteractive

# Install base tools, Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    ca-certificates \
    python3 \
    python3-pip \
    python3-psutil \
    python3-distro \
    python3-z3 \
    python3-numpy \
    python3-pandas \
    python3-matplotlib \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libgmp-dev \
    libtinfo6 \
    libopenblas-dev \
 && rm -rf /var/lib/apt/lists/*

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install OpenJDK and sbt (Scala build tool)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg \
    apt-transport-https \
    ca-certificates \
    curl \
 && mkdir -p /etc/apt/keyrings \
 && curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x99E82A75642AC823" \
    | gpg --dearmor -o /etc/apt/keyrings/sbt-archive-keyring.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/sbt-archive-keyring.gpg] https://repo.scala-sbt.org/scalasbt/debian all main" > /etc/apt/sources.list.d/sbt.list \
 && echo "deb [signed-by=/etc/apt/keyrings/sbt-archive-keyring.gpg] https://scala.jfrog.io/artifactory/debian all main" > /etc/apt/sources.list.d/scala.list \
 && apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jdk \
    sbt \
 && rm -rf /var/lib/apt/lists/*

# (Optional) JAVA_HOME is not strictly required for sbt, but some tools expect it.
# We set it dynamically at shell init time to support multiple architectures.
RUN echo 'export JAVA_HOME="$(dirname $(dirname $(readlink -f $(which javac))))"' > /etc/profile.d/java_home.sh \
 && chmod +x /etc/profile.d/java_home.sh

WORKDIR /workspace

# Clone SHIR repo branches into separate subdirectories
RUN git clone -b routable-network-setup --single-branch --depth 1 --recursive --shallow-submodules https://bitbucket.org/cdubach/shir /workspace/shir-routable-network-setup
RUN git clone -b routable-network-marked --single-branch --depth 1 --recursive --shallow-submodules https://bitbucket.org/cdubach/shir /workspace/shir-routable-network-marked


# Precompile the test suites for all branches
RUN cd /workspace/shir-routable-network-setup && sbt test:compile
RUN cd /workspace/shir-routable-network-marked && sbt test:compile

# Copy the repo into the container
# COPY --chown=${USERNAME}:${USERNAME} . /workspace
COPY . /workspace

# Set up permission
RUN chmod -R 777 /workspace

# Default command: run all eqsat and lowering.
# Results are written to /workspace/results.
CMD ["/bin/bash", "-lc", "set -euo pipefail; python3 evaluation.py"]
