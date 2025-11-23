# Running ds-test in Docker

This guide shows you how to run the ds-test project in a Docker container with Ubuntu.

## Prerequisites

- Docker Desktop installed on Windows
- Docker daemon running

## Quick Start

### Option 1: Using the provided script (Linux/Mac/WSL)

```bash
chmod +x docker-run.sh
./docker-run.sh
```

### Option 2: Manual steps (Windows PowerShell or any OS)

#### Step 1: Build the Docker image

```bash
docker build -t ds-test .
```

This creates a Docker image named `ds-test` with Ubuntu and all required dependencies.

#### Step 2: Run the container

```bash
docker run -it --rm ds-test
```

This starts an interactive bash shell inside the container.

#### Step 3: Inside the container, run your tests

```bash
# You're now inside the Ubuntu container at /app directory
python3 ds_test.py "python3 client.py" -n -p 50000 -c TestConfigs
```

## Alternative: Run the test directly

You can run the test command directly without entering the container:

```bash
docker run -it --rm ds-test python3 ds_test.py "python3 client.py" -n -p 50000 -c TestConfigs
```

## Troubleshooting

### If you get "permission denied" errors:

Make sure the executables are set properly:
```bash
docker run -it --rm ds-test bash -c "chmod +x ds-server ds-client && python3 ds_test.py 'python3 client.py' -n -p 50000 -c TestConfigs"
```

### To access the container for debugging:

```bash
docker run -it --rm ds-test /bin/bash
```

Then you can manually test:
```bash
ls -la
file ds-server
ldd ds-server
./ds-server -c TestConfigs/config10-long-med.xml -v brief
```

### To copy results out of the container:

First, run the container with a name:
```bash
docker run -it --name ds-test-run ds-test python3 ds_test.py "python3 client.py" -n -p 50000 -c TestConfigs
```

Then copy the results:
```bash
docker cp ds-test-run:/app/results ./results-from-docker
docker rm ds-test-run
```

## Building with different Ubuntu versions

If the executables don't work with Ubuntu 22.04, try Ubuntu 20.04:

Edit the Dockerfile and change the first line to:
```dockerfile
FROM ubuntu:20.04
```

Then rebuild:
```bash
docker build -t ds-test .
```

## Cleanup

Remove the Docker image when done:
```bash
docker rmi ds-test
```

Remove all stopped containers:
```bash
docker container prune
```

