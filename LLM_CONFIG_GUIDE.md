# LLM Configuration Guide

The Coding Agent supports multiple LLM providers with a flexible configuration system. API keys can be added via JSON configuration file using direct keys or environment variable references.

## Overview

This guide explains how to configure API keys for different LLM providers using the `llm_config.json` file. The configuration system supports multiple provider profiles and automatic environment variable substitution.

## JSON File Location

- **Path**: `llm_config.json` in the project root (`/Users/anant/Documents/repos/Coding-Agent/`)
- **Default**: Automatically loads from project root if exists
- **Example template**: `llm_config.json.example`

## Supported Providers

- **Gemini** (Google) - Default provider
- **OpenRouter** - Access to multiple models via unified API (e.g., DeepSeek, GPT-4, Claude)
- **OpenAI** - Direct OpenAI API access
- **GLM** - GLM 4.6 with custom URL support

## JSON Structure

### Basic Structure

```json
{
  "providers": {
    "profile-name": {
      "provider": "provider-type",
      "api_key": "your-api-key-here",
      "model": "model-name",
      "base_url": "optional-custom-url"
    }
  },
  "default_profile": "profile-name"
}
```

### Method 1: Direct API Keys (Not Recommended)

```json
{
  "providers": {
    "gemini-direct": {
      "provider": "gemini",
      "api_key": "AIzaSyD...",
      "model": "gemini-2.5-flash"
    }
  },
  "default_profile": "gemini-direct"
}
```

**⚠️ Security Warning**: Direct API keys in JSON files can be accidentally committed to version control. Use environment variables instead.

### Method 2: Environment Variable References (Recommended)

```json
{
  "providers": {
    "gemini-default": {
      "provider": "gemini",
      "api_key": "${GEMINI_API_KEY}",
      "model": "gemini-2.5-flash"
    }
  },
  "default_profile": "gemini-default"
}
```

**✅ Recommended**: API keys reference environment variables using `${ENV_VAR_NAME}` syntax, keeping sensitive data out of configuration files.

## Provider-Specific Configuration

### 1. Gemini (Google)

```json
"gemini-profile": {
  "provider": "gemini",
  "api_key": "${GEMINI_API_KEY}",
  "model": "gemini-2.5-flash"
}
```

**Required environment variable**: `GEMINI_API_KEY`

**Available models**: `gemini-2.5-flash`, `gemini-1.5-flash`

### 2. OpenRouter

```json
"openrouter-profile": {
  "provider": "openrouter",
  "api_key": "${OPENROUTER_API_KEY}",
  "model": "deepseek/deepseek-chat-v3.1:free",
  "base_url": "https://openrouter.ai/api/v1"
}
```

**Required environment variable**: `OPENROUTER_API_KEY`

**Available models**: `deepseek/deepseek-chat-v3.1:free`, `openai/gpt-4-turbo`, `anthropic/claude-3-sonnet`

### 3. OpenAI

```json
"openai-profile": {
  "provider": "openai",
  "api_key": "${OPENAI_API_KEY}",
  "model": "gpt-4o",
  "base_url": "https://api.openai.com/v1"
}
```

**Required environment variable**: `OPENAI_API_KEY`

**Available models**: `gpt-4o`, `gpt-4-turbo`, `gpt-5-codex`

### 4. GLM

```json
"glm-profile": {
  "provider": "glm",
  "api_key": "${GLM_API_KEY}",
  "model": "glm-4-6",
  "base_url": "https://api.z.ai/api/coding/paas/v4"
}
```

**Required environment variable**: `GLM_API_KEY`

**Available models**: `glm-4-6`

## Complete Example Configuration

```json
{
  "providers": {
    "gemini-default": {
      "provider": "gemini",
      "api_key": "${GEMINI_API_KEY}",
      "model": "gemini-2.5-flash"
    },
    "openrouter-deepseek": {
      "provider": "openrouter",
      "api_key": "${OPENROUTER_API_KEY}",
      "model": "deepseek/deepseek-chat-v3.1:free",
      "base_url": "https://openrouter.ai/api/v1"
    },
    "openai-gpt4": {
      "provider": "openai",
      "api_key": "${OPENAI_API_KEY}",
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1"
    },
    "glm-custom": {
      "provider": "glm",
      "api_key": "${GLM_API_KEY}",
      "model": "glm-4-6",
      "base_url": "https://your-glm-endpoint.com"
    }
  },
  "default_profile": "gemini-default"
}
```

## Setup Steps

1. **Create or edit** `llm_config.json` in project root
2. **Set environment variables**:
   ```bash
   export GEMINI_API_KEY="your-key-here"
   export OPENROUTER_API_KEY="your-key-here"
   export OPENAI_API_KEY="your-key-here"
   export GLM_API_KEY="your-key-here"
   ```
3. **Reference them** in JSON using `${ENV_VAR_NAME}` syntax
4. **Set default_profile** to the profile name you want as default

## Security Best Practices

1. **Never commit API keys** directly in JSON - use environment variables
2. **Use `${ENV_VAR}` syntax** instead of hardcoding keys
3. **Add `llm_config.json` to `.gitignore`** if containing direct keys
4. **Keep `llm_config.json.example`** as template (already exists)
5. **Set environment variables** in shell profile (`.bashrc`, `.zshrc`) or use `.env` files

## Validation

The system automatically:
- Validates JSON structure on load
- Checks for required fields: `provider`, `api_key`, `model`
- Validates provider names against supported list
- Substitutes environment variables on load
- Warns if environment variable is not set

## Configuration Methods

### Method 1: Configuration File (Recommended)

Use the `llm_config.json` file as described above. The system automatically loads profiles from this file.

### Method 2: Command Line Arguments

Use `--provider`, `--api-token`, and `--model` flags directly:

```bash
python run_conversion.py \
  --provider openrouter \
  --api-token "YOUR_OPENROUTER_KEY" \
  --model "deepseek/deepseek-chat-v3.1:free" \
  --github-url "https://github.com/owner/repo"
```

You can also use a profile from the config file:
```bash
python run_conversion.py \
  --profile openrouter-deepseek \
  --github-url "https://github.com/owner/repo"
```

## Usage Examples

### Using OpenRouter with DeepSeek (Free Model)

```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --provider openrouter \
  --api-token "YOUR_OPENROUTER_API_KEY" \
  --model "deepseek/deepseek-chat-v3.1:free"
```

Or with config file:
```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --profile openrouter-deepseek \
  --model "deepseek/deepseek-chat-v3.1:free"
```

### Using OpenAI GPT-5 Codex

```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --provider openai \
  --api-token "YOUR_OPENAI_API_KEY" \
  --model "gpt-5-codex"
```

### Using GLM 4.6 with Custom URL

```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --provider glm \
  --api-token "YOUR_GLM_API_KEY" \
  --model "glm-4-6" \
  --llm-base-url "https://your-glm-endpoint.com"
```

### Using Gemini (Default)

```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --api-token "YOUR_GEMINI_API_KEY" \
  --model "gemini-2.5-flash"
```

## Usage with Configuration File

- **Default profile**: Used automatically if no profile specified when running scripts
- **Specific profile**: Use `--profile profile-name` in command line to use a specific profile
- **Override model**: Use `--model model-name` to override the profile's default model

Example:
```bash
python run_conversion.py \
  --github-url "https://github.com/owner/repo" \
  --profile openrouter-deepseek
```

## Model Formats by Provider

- **Gemini**: `gemini-2.5-flash`, `gemini-1.5-flash`
- **OpenRouter**: `deepseek/deepseek-chat-v3.1:free`, `openai/gpt-4-turbo`, `anthropic/claude-3-sonnet`
- **OpenAI**: `gpt-4o`, `gpt-4-turbo`, `gpt-5-codex`
- **GLM**: `glm-4-6`

## Environment Variables

Set API keys as environment variables for security:

```bash
export GEMINI_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GLM_API_KEY="your-key"
```

Then reference them in `llm_config.json` using `${VARIABLE_NAME}`.

The configuration is loaded by `LLMConfigManager` in `src/config/llm_config_manager.py` which handles environment variable substitution automatically.

## Backward Compatibility

The agent maintains backward compatibility with the old `--api-token` and `gemini_api_token` parameters. If you don't specify `--provider`, it defaults to Gemini.

