# REMEMBER TO OPEN THE NECESSARY PORTS FOR I4.0!!!!
# The ports are 8060 (I4.0 Server), 8061 (I4.0 Files Server), 8062 (I4.0 Data Share Server)

# An I4.0 config file will be created, then you will be able to edit
# To edit the config file (or anything inside the container), please write on your OS terminal `docker exec -it <CONTAINER NAME> /bin/bash`

FROM python:3.12.5-slim-bookworm

# Set the workdir
WORKDIR /I4.0
ENV I4_WORKDIR="/I4.0"

# Install some dependencies
RUN apt-get update
RUN apt-get install -y apt-utils pciutils python3-pip python3-venv git vim nano build-essential mesa-utils libgl1-mesa-dev libglib2.0-dev libglib2.0-0

# Copy the required files
COPY requirements.txt .
COPY requirements_optional.txt .
COPY DockerUtils/install_dependencies.sh .

# Install the requirements
RUN sh install_dependencies.sh

# Execute I4.0
CMD ["python3", "ai_server.py"]