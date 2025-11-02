# Docker Quick Start Guide

Get the Java to Node.js Conversion Agent running in Docker in under 2 minutes!

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- API key from one of: Gemini, OpenRouter, OpenAI, or GLM

## 🚀 Quick Start (3 Steps)

### 1. Set Your API Key

The Docker setup **automatically loads** variables from your `.zshrc` or `.bashrc`! Just run:

```bash
# That's it! If you have variables in .zshrc, they're automatically loaded!
./docker-run.sh start
```

**Or manually set:**

```bash
# Option A: Export as environment variable
export GEMINI_API_KEY=your_api_key_here

# Option B: Create .env file (recommended)
echo "GEMINI_API_KEY=your_api_key_here" > .env

# Option C: Sync from .zshrc to .env
./sync-env-from-zshrc.sh
```

**Variables supported:**
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `GLM_API_KEY`
- `GLM_BASE_URL`

### 2. Start the Service

```bash
# Make helper script executable (first time only)
chmod +x docker-run.sh

# Start the API server
./docker-run.sh start
```

### 3. Open Web UI

Open your browser: **http://localhost:8000**

That's it! 🎉

## Common Commands

```bash
# View logs
./docker-run.sh logs

# Check status
./docker-run.sh status

# Stop server
./docker-run.sh stop

# Run CLI conversion
./docker-run.sh convert \
  --github-url "https://github.com/owner/repo" \
  --api-token "your_token" \
  --model "gemini-2.5-flash"
```

## Alternative: Direct Docker Commands

If you prefer using docker-compose directly:

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Running a Conversion

### Via Web UI (Easiest)

1. Open http://localhost:8000
2. Enter your API token and model
3. Enter GitHub repository URL
4. Click "Start Conversion"
5. Monitor progress in real-time

### Via CLI

```bash
./docker-run.sh convert \
  --github-url "https://github.com/janjakovacevic/SakilaProject" \
  --api-token "$GEMINI_API_KEY" \
  --model "gemini-2.5-flash" \
  --framework express \
  --orm sequelize
```

## Output Files

Converted projects are saved to: `./outputs/` directory

```bash
ls -la outputs/
```

## Configuration

### Using .env File

Create `.env` file in project root:

```env
GEMINI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Using Config File

```bash
# Copy example config
cp llm_config.json.example llm_config.json

# Edit with your keys
nano llm_config.json

# Config will be automatically mounted
```

## Troubleshooting

### Port Already in Use

Change port in `.env`:
```env
API_PORT=8001
```

Then restart:
```bash
./docker-run.sh restart
```

### Container Won't Start

Check logs:
```bash
./docker-run.sh logs
```

### API Key Not Working

1. Verify key is set: `echo $GEMINI_API_KEY`
2. Check logs for specific errors
3. Ensure key has proper permissions/quota

### Permission Errors

```bash
mkdir -p outputs tmp
chmod 755 outputs tmp
```

## All Helper Script Commands

```bash
./docker-run.sh build      # Build Docker image
./docker-run.sh start      # Start API server
./docker-run.sh stop       # Stop server
./docker-run.sh restart    # Restart server
./docker-run.sh logs       # View logs
./docker-run.sh status     # Check status
./docker-run.sh convert    # Run CLI conversion
./docker-run.sh shell      # Open container shell
./docker-run.sh clean      # Remove containers/images
./docker-run.sh help      # Show help
```

## Next Steps

- Read [DOCKER.md](./DOCKER.md) for detailed documentation
- Check [USAGE.md](./USAGE.md) for conversion examples
- Visit API docs: http://localhost:8000/docs

## Support

For issues or questions:
1. Check logs: `./docker-run.sh logs`
2. Review [DOCKER.md](./DOCKER.md) troubleshooting section
3. Check GitHub issues
