# How to Use the Java to Node.js Conversion Agent

## Where to Provide Gemini API Token and GitHub URL

There are **two main ways** to provide the Gemini API token and GitHub URL:

---

## Option 1: Via REST API (Recommended for Production)

### Step 1: Start the API Server

```bash
cd /Users/anant/Documents/repos/Coding-Agent
python -m src.api.server
```

The server will start on `http://localhost:8000`

### Step 2: Make a POST Request to `/api/convert`

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "gemini_api_token": "YOUR_GEMINI_API_TOKEN",
    "github_url": "https://github.com/owner/repo",
    "target_framework": "express",
    "orm_choice": "sequelize"
  }'
```

**Using Python requests:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/convert",
    json={
        "gemini_api_token": "YOUR_GEMINI_API_TOKEN",
        "github_url": "https://github.com/owner/repo",
        "target_framework": "express",  # or "nestjs"
        "orm_choice": "sequelize"  # or "typeorm"
    }
)

job_id = response.json()["job_id"]
print(f"Conversion started with job ID: {job_id}")
```

**Using JavaScript/fetch:**
```javascript
const response = await fetch('http://localhost:8000/api/convert', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    gemini_api_token: 'YOUR_GEMINI_API_TOKEN',
    github_url: 'https://github.com/owner/repo',
    target_framework: 'express',
    orm_choice: 'sequelize'
  })
});

const { job_id } = await response.json();
console.log('Job ID:', job_id);
```

### Step 3: Check Status

```bash
# Get job status
curl "http://localhost:8000/api/convert/{job_id}"

# Get metadata
curl "http://localhost:8000/api/convert/{job_id}/metadata"

# Download converted project (when completed)
curl "http://localhost:8000/api/convert/{job_id}/download" -o converted-project.zip
```

---

## Option 2: Direct Code Usage (For Testing/Development)

### In Test Files

Edit `/Users/anant/Documents/repos/Coding-Agent/src/tests/test_full_conversion.py`:

```python
import os
from src.agents.orchestrator import create_conversion_workflow, ConversionState

def test_complete_conversion():
    """Test end-to-end conversion"""
    
    workflow = create_conversion_workflow()
    
    initial_state = ConversionState(
        github_url="https://github.com/owner/repo",  # ← Your GitHub URL here
        gemini_api_token=os.getenv("GEMINI_API_TOKEN") or "YOUR_API_TOKEN",  # ← Your API token here
        target_framework="express",
        orm_choice="sequelize",
        repo_path=None,
        file_map=None,
        metadata=None,
        converted_components={},
        output_path=None,
        validation_result=None,
        errors=[]
    )
    
    # Execute workflow
    result = workflow.invoke(initial_state)
    
    print(f"Conversion completed!")
    print(f"Output path: {result['output_path']}")
    print(f"Valid: {result['validation_result']['valid']}")
```

### Using Environment Variable

Set the API token as an environment variable:

```bash
export GEMINI_API_TOKEN="your-api-token-here"
```

Then in your code:
```python
import os
gemini_api_token = os.getenv("GEMINI_API_TOKEN")
```

---

## Option 3: Direct Python Script

Create a script `run_conversion.py`:

```python
#!/usr/bin/env python3
"""Direct conversion script"""

import os
from src.agents.orchestrator import create_conversion_workflow, ConversionState

# SET YOUR VALUES HERE:
GEMINI_API_TOKEN = "YOUR_GEMINI_API_TOKEN"  # ← Your API token
GITHUB_URL = "https://github.com/owner/repo"  # ← Your GitHub URL

def main():
    workflow = create_conversion_workflow()
    
    initial_state = ConversionState(
        github_url=GITHUB_URL,
        gemini_api_token=GEMINI_API_TOKEN,
        target_framework="express",
        orm_choice="sequelize",
        repo_path=None,
        file_map=None,
        metadata=None,
        converted_components={},
        output_path=None,
        validation_result=None,
        errors=[]
    )
    
    print("Starting conversion...")
    result = workflow.invoke(initial_state)
    
    print(f"\n✅ Conversion completed!")
    print(f"📁 Output: {result['output_path']}")
    print(f"✅ Valid: {result['validation_result']['valid']}")
    
    if result.get('errors'):
        print(f"\n⚠️  Errors: {result['errors']}")

if __name__ == "__main__":
    main()
```

Run it:
```bash
python run_conversion.py
```

---

## Summary

**Key Locations:**

1. **API Server** (`src/api/server.py`):
   - Line 17-21: `ConversionRequest` model defines where API token and URL are received
   - Line 55-61: Values are passed to `run_conversion()` function
   - Line 158-170: Values are used to create `ConversionState`

2. **Direct Usage** (test files or scripts):
   - Create `ConversionState` with `github_url` and `gemini_api_token` fields
   - Pass to `workflow.invoke(initial_state)`

3. **Environment Variables**:
   - Set `GEMINI_API_TOKEN` environment variable
   - Access via `os.getenv("GEMINI_API_TOKEN")`

---

## Getting Your Gemini API Token

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API token (the API key you receive)

**⚠️ Security Note:** Never commit your API token to version control. Use environment variables or secure configuration files.

