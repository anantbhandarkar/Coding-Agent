# Quick Start Guide - SakilaProject Conversion

## ✅ Prerequisites Verified

- ✅ Python 3.14.0 installed
- ✅ Git 2.39.5 available
- ✅ Virtual environment set up at `venv/`
- ✅ All dependencies installed
- ✅ Conversion script verified
- ✅ GitHub repository accessible: https://github.com/janjakovacevic/SakilaProject

## 🚀 Ready to Execute

### Option 1: Use Docker (Recommended - Easiest)

```bash
cd /Users/anant/Documents/repos/Coding-Agent
./docker-run.sh convert \
  --github-url "https://github.com/janjakovacevic/SakilaProject" \
  --profile glm-4-6-zai \
  --output "/path/to/output"
```

Or use the build-and-run script:
```bash
./build-and-run.sh
```

### Option 2: Use CLI Directly

```bash
cd /Users/anant/Documents/repos/Coding-Agent
source venv/bin/activate

# Model is now REQUIRED
python run_conversion.py \
  --github-url "https://github.com/janjakovacevic/SakilaProject" \
  --api-token "YOUR_GEMINI_API_TOKEN" \
  --model "gemini-2.5-flash" \
  --framework express \
  --orm sequelize

# With NestJS and TypeORM
python run_conversion.py \
  --github-url "https://github.com/janjakovacevic/SakilaProject" \
  --api-token "YOUR_GEMINI_API_TOKEN" \
  --model "gemini-2.5-flash" \
  --framework nestjs \
  --orm typeorm
```

### Available Gemini Models

Common models you can specify:
**Available models (REQUIRED - must specify):**
- `gemini-2.5-flash` - Latest, fast (recommended)
- `gemini-1.5-flash` - Previous generation, still available
- `gemini-2.0-flash-exp` - Experimental
- Note: `gemini-1.5-pro` is deprecated and no longer available

**Important:** The `--model` parameter is now REQUIRED. You must specify a model when running conversions.

### Option 3: Start API Server (Web UI)

```bash
cd /Users/anant/Documents/repos/Coding-Agent
source venv/bin/activate
python -m src.api.server
```

Then open http://localhost:8000 in your browser.

## 📝 Next Steps

1. **Get your Gemini API token** from https://makersuite.google.com/app/apikey
2. **Run the conversion** using one of the methods above
3. **Wait for completion** (may take 10-30 minutes depending on repository size)
4. **Check output directory** for converted Node.js project

## 📊 Expected Output Location

- Default: `/tmp/conversion-output-{uuid}/`
- Custom: Use `--output` flag to specify directory

## 🔍 Verify Repository

The SakilaProject repository has been verified:
- ✅ Repository is public and accessible
- ✅ Default branch: `master`
- ✅ Build system: Maven (detected from pom.xml)

## 📚 For More Details

See the full plan document: `execute-sakilaproject-conversion.plan.md`

