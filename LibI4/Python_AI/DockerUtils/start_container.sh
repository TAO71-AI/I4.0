#!/bin/bash

CONTAINER_EXISTS=$(docker images --filter "reference=i4.0" --format "{{.Repository}}:{{.Tag}}")
GPU_INFO=$(lspci -nn | grep -E "VGA|3D|Display")

if [ -n "$CONTAINER_EXISTS" ]; then
    echo "Starting I4.0..."
    
    if echo "$GPU_INFO" | grep -i nvidia; then
        # Execute I4.0 for NVIDIA GPUs
        docker run -it --gpus all -v $(pwd):/I4.0 -p 8060:8060 -p 8061:8061 i4.0
    elif echo "$GPU_INFO" | grep -i amd; then
        # Execute I4.0 for AMD GPUs
        docker run -it --device=/dev/kfd --device=/dev/dri -v $(pwd):/I4.0 -p 8060:8060 -p 8061:8061 i4.0
    else
        # Execute I4.0 without GPU (only CPU)
        docker run -it -v $(pwd):/I4.0 -p 8060:8060 -p 8061:8061 i4.0
    fi
else
    echo "The I4.0 container doesn't exists. Creating, then running this script."
    echo "Make sure you're on the Python_AI directory."

    # Clear docker
    docker container prune
    docker image prune

    # Build I4.0 container
    docker build -t i4.0 .

    # Check the output
    if [ $? -eq 0 ]; then
        # I4.0 container built successfully
        echo "I4.0 container successfully built, restarting script..."

        # Execute this script again
        exec "$0" "$@"
    else
        # Error building I4.0
        echo "Error building I4.0 container."
        exit $?
    fi
fi