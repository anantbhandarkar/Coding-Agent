# Docker Setup Guide

This guide explains how to run the Java to Node.js Conversion Agent using Docker.

## Prerequisites

- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)
- Git (for cloning repositories during conversion)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Start the service:**
   ```bash
   docker-compose up -d
   ```

2. **Access the web UI:**
   Open your browser at: http://localhost:8000

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t java-to-nodejs-converter .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name converter \
     -p 8000:8000 \
     -v $(pwd)/outputs:/app/outputs \
     -v $(pwd)/tmp:/app/tmp \
     java-to-nodejs-converter
   ```

3. **Access the service:**
   Open http://localhost:8000 in your browser

4. **View logs:**
   ```bash
   docker logs -f converter
   ```

## Configuration

### Using Environment Variables

You can configure the LLM provider via environment variables. Create a `.env` file:

```env
# For Gemini
GEMINI_API_KEY=your_gemini_api_key

# For OpenRouter
OPENROUTER_API_KEY=your_openrouter_key

# For OpenAI
OPENAI_API_KEY=your_openai_key

# For GLM
GLM_API_KEY=your_glm_key
GLM_BASE_URL=https://your-glm-endpoint.com
```

Then update `docker-compose.yml` to use the `.env` file, or pass them directly:

```bash
docker run -d \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e PYTHONUNBUFFERED=1 \
  -v $(pwd)/outputs:/app/outputs \
  java-to-nodejs-converter
```

### Using Config File

1. Copy the example config:
   ```bash
   cp llm_config.json.example llm_config.json
   ```

2. Edit `llm_config.json` with your API keys

3. Mount it in docker-compose.yml (already configured) or via volume:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -v $(pwd)/llm_config.json:/app/llm_config.json:ro \
     -v $(pwd)/outputs:/app/outputs \
     java-to-nodejs-converter
   ```

## Running Commands

### Run API Server (Default)

```bash
docker-compose up
# or
docker run java-to-nodejs-converter api
```

### Run CLI Conversion

You can run the CLI conversion tool directly:

```bash
docker run --rm \
  -v $(pwd)/outputs:/app/outputs \
  -e GEMINI_API_KEY=your_key \
  java-to-nodejs-converter convert \
    --github-url "https://github.com/owner/repo" \
    --api-token "your_token" \
    --model "gemini-2.5-flash" \
    --framework express \
    --orm sequelize
```

### Execute Custom Commands

```bash
docker run --rm java-to-nodejs-converter python -c "print('Hello')"
```

## Volume Mounts

The Docker setup mounts these directories:

- `./outputs` → `/app/outputs` - Converted projects are saved here
- `./tmp` → `/app/tmp` - Temporary files during conversion
- `./llm_config.json` → `/app/llm_config.json` - LLM configuration (read-only)

## Persistent Data

All converted projects are saved to the `./outputs` directory on your host machine, so they persist even after container removal.

## Health Check

The container includes a health check that verifies the API is responding:

```bash
# Check container health
docker ps
# Look for "healthy" status

# Manual health check
curl http://localhost:8000/docs
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
# or
docker logs converter
```

### Port already in use

Change the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Permission issues with volumes

Ensure the `outputs` and `tmp` directories exist and have write permissions:
```bash
mkdir -p outputs tmp
chmod 755 outputs tmp
```

### API token not working

1. Verify your API token is correct
2. Check if it's set in the environment or config file
3. View container logs for specific error messages

### Conversion fails

1. Check container logs: `docker logs converter`
2. Verify the GitHub repository URL is accessible
3. Ensure you have sufficient API quota/credits
4. Check the `outputs` directory for error logs

## Development

### Rebuild after code changes

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Run with live code reload (for development)

Mount the source code as a volume:

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  conversion-agent:
    volumes:
      - .:/app
      - ./outputs:/app/outputs
```

Then run: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

## Production Considerations

For production deployment:

1. **Use environment variables** for secrets (never commit `.env` or `llm_config.json` with keys)
2. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```
3. **Use reverse proxy** (nginx/traefik) for HTTPS
4. **Enable logging** to external service (e.g., CloudWatch, Datadog)
5. **Backup outputs directory** regularly

## Examples

### Example 1: Quick test conversion

```bash
docker run --rm \
  -v $(pwd)/outputs:/app/outputs \
  -e GEMINI_API_KEY=your_key \
  java-to-nodejs-converter convert \
    --github-url "https://github.com/janjakovacevic/SakilaProject" \
    --api-token "your_key" \
    --model "gemini-2.5-flash" \
    --framework express \
    --orm sequelize
```

### Example 2: Run with custom config

```bash
docker run -d \
  --name converter \
  -p 8000:8000 \
  -v $(pwd)/my-llm-config.json:/app/llm_config.json:ro \
  -v $(pwd)/outputs:/app/outputs \
  java-to-nodejs-converter
```

### Example 3: Background service with auto-restart

```bash
docker run -d \
  --name converter \
  --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  -e GEMINI_API_KEY=your_key \
  java-to-nodejs-converter
```

