# Docker Guide for Web Image Scraper

This document provides instructions for setting up, running, and managing the Docker environment for the Web Image Scraper project using direct Docker commands.

## Prerequisites

- Docker installed on your system
- Sudo access (all commands in this guide use `sudo`)

## Project Structure

Ensure your project directory looks like this:

```
image-citations/
├── Dockerfile
├── requirements.txt
├── main.py
├── .env
└── DOCKER.md (this file)
```

## Docker Commands

### Building the Docker Image

To build the Docker image:

```bash
sudo docker build -t web-image-scraper .
```

### Viewing Docker Images

To see all Docker images:

```bash
sudo docker images
```

### Running the Container

To start the container in interactive mode:

```bash
sudo docker run -it --rm -v $(pwd):/app -v $(pwd)/images:/app/images web-image-scraper bash
```

This command does the following:
- `-it`: Runs the container interactively
- `--rm`: Removes the container when it exits
- `-v $(pwd):/app`: Mounts the current directory to /app in the container
- `-v $(pwd)/images:/app/images`: Mounts the images directory
- `--env-file .env`: Uses the environment variables from .env file
- `web-image-scraper`: The name of our image
- `bash`: The command to run inside the container

### Viewing Running Containers

To see all running containers:

```bash
sudo docker ps
```

### Stopping a Container

To stop a running container:

```bash
sudo docker stop <CONTAINER_ID>
```

### Removing a Container

To remove a stopped container:

```bash
sudo docker rm <CONTAINER_ID>
```

### Removing an Image

To remove the Docker image:

```bash
sudo docker rmi web-image-scraper
```

### Complete Cleanup

To stop all running containers, remove all containers, and remove the image:

```bash
sudo docker stop $(sudo docker ps -aq)
sudo docker rm $(sudo docker ps -aq)
sudo docker rmi web-image-scraper
```

## Running the Script

Once inside the container:

```bash
python main.py <URL> -o /app/images -m <MIN_AREA>
```

Example:
```bash
python main.py https://www.ai21.com/blog/the-promise-of-rag-bringing-enterprise-generative-ai-to-life -o /app/images -m 50000
```

## Notes

- Always use `sudo` with Docker commands if you're not in the Docker group.
- The `/app/images` directory in the container is mapped to the `./images` directory on your host machine.
- Make sure to keep your `.env` file secure and never commit it to version control.

## Troubleshooting

If you encounter issues:

1. Ensure your `.env` file is present and contains the `SCRAPINGBEE_API_KEY`.
2. Verify that all required files (Dockerfile, main.py, requirements.txt) are present and correctly configured.
3. Check the Docker logs for any error messages:
   ```bash
   sudo docker logs <CONTAINER_ID>
   ```
4. If changes are made to the Dockerfile or requirements, rebuild the image:
   ```bash
   sudo docker build -t web-image-scraper .
   ```