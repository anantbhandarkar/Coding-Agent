# Environment Variables Setup for Docker

This guide explains how to use your existing environment variables (from `.zshrc` or `.bashrc`) with Docker containers.

## Quick Start

The Docker setup automatically loads environment variables from your shell profile (`.zshrc` or `.bashrc`). Just run:

```bash
./docker-run.sh start
```

The script will automatically detect and load your API keys!

## Methods (Choose One)

### Method 1: Automatic Loading from Shell Profile (Recommended)

The `docker-run.sh` script automatically:
- ✅ Checks for variables already exported in your current shell
- ✅ Loads from `.zshrc` (if exists)
- ✅ Falls back to `.bashrc` (if exists)
- ✅ Uses `.env` file if it exists (takes precedence)

**Just run:**
```bash
./docker-run.sh start
```

### Method 2: Sync to .env File

If you prefer using a `.env` file:

```bash
# Sync your .zshrc variables to .env file
./sync-env-from-zshrc.sh

# Then start Docker
./docker-run.sh start
```

This creates a `.env` file from your `.zshrc` exports. The `.env` file takes precedence over shell profile variables.

### Method 3: Manual .env File

Create a `.env` file manually in the project root:

```bash
# .env
GEMINI_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
OPENAI_API_KEY=your_openai_key_here
GLM_API_KEY=your_glm_key_here
GLM_BASE_URL=https://your-glm-endpoint.com  # Optional
```

Then:
```bash
./docker-run.sh start
```

### Method 4: Export Before Running

Export variables in your current shell session:

```bash
export GEMINI_API_KEY=your_key_here
export OPENROUTER_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
export GLM_API_KEY=your_key_here

./docker-run.sh start
```

## Variable Priority

The order of precedence (highest to lowest):

1. **Variables already exported in current shell**
2. **`.env` file** (if exists)
3. **`.zshrc` or `.bashrc`** (automatically loaded by script)
4. **docker-compose.yml environment defaults** (empty if not set)

## Required Variables

The following environment variables are used:

- `GEMINI_API_KEY` - Google Gemini API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `OPENAI_API_KEY` - OpenAI API key
- `GLM_API_KEY` - GLM API key
- `GLM_BASE_URL` - GLM base URL (optional)

You only need to set the ones you plan to use.

## Verification

Check if variables are loaded:

```bash
# Check what docker-run.sh will see
./docker-run.sh start

# The script will show messages like:
# ℹ Loaded 3 environment variable(s) from shell profile
# OR
# ℹ Loaded environment variables from .env file
```

## Troubleshooting

### Variables Not Loading from .zshrc

If variables aren't being detected:

1. **Verify your `.zshrc` format:**
   ```bash
   # Make sure they're exported like this:
   export GEMINI_API_KEY="your_key_here"
   export OPENROUTER_API_KEY="your_key_here"
   ```

2. **Check if variables are in your profile:**
   ```bash
   grep -E "export.*API_KEY" ~/.zshrc
   ```

3. **Try the sync script:**
   ```bash
   ./sync-env-from-zshrc.sh
   ./docker-run.sh start
   ```

### Variables Not Passed to Container

If variables aren't reaching the container:

1. **Check docker-compose.yml** - Make sure it has `env_file: - .env`
2. **Verify .env file exists** - Run `./sync-env-from-zshrc.sh` if needed
3. **Check container logs:**
   ```bash
   ./docker-run.sh logs
   ```

### Container Can't Access Variables

The container needs the variables to be explicitly passed. The `docker-compose.yml` uses:

```yaml
env_file:
  - .env
environment:
  - GEMINI_API_KEY=${GEMINI_API_KEY:-}
  # ... etc
```

This ensures variables from `.env` OR your shell are passed to the container.

## Examples

### Example 1: Using .zshrc (Automatic)

```bash
# Your .zshrc contains:
export GEMINI_API_KEY="AIzaSy..."
export OPENROUTER_API_KEY="sk-or-..."

# Just run:
./docker-run.sh start
# ✓ Variables automatically loaded!
```

### Example 2: Creating .env from .zshrc

```bash
# Sync to .env
./sync-env-from-zshrc.sh

# Output:
# ℹ Found .zshrc at /Users/you/.zshrc
# ✓ Found GEMINI_API_KEY
# ✓ Found OPENROUTER_API_KEY
# ✓ Created/updated .env

# Start Docker
./docker-run.sh start
```

### Example 3: Manual .env File

```bash
# Create .env
cat > .env << EOF
GEMINI_API_KEY=AIzaSy...
OPENROUTER_API_KEY=sk-or-...
EOF

# Start Docker
./docker-run.sh start
```

## Security Notes

- ✅ **Never commit `.env` file** to version control (already in `.gitignore`)
- ✅ **Use environment variables** instead of hardcoding keys
- ✅ **Keep your `.zshrc` secure** - it contains your API keys
- ✅ **The `.env` file** is automatically ignored by git

## Docker Compose Integration

The `docker-compose.yml` file is configured to:

1. Read from `.env` file (if exists)
2. Override with shell environment variables (if set)
3. Pass all variables to the container

This means you can use any of the methods above and they'll work seamlessly!

