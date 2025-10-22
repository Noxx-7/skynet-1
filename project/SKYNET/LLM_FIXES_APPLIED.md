# LLM Model Fixes Applied

## Issues Fixed

### 1. OpenAI Models
**Problem:**
- Users were seeing errors for deprecated models (gpt-4-turbo-preview, gpt-4)
- Quota exceeded errors for gpt-3.5-turbo even with fresh API keys

**Solution:**
- Updated model registry to include all currently available OpenAI models
- Added newer models: GPT o1, GPT o1-mini
- Kept existing models: gpt-4o, gpt-4o-mini (these are the recommended models)
- The deprecated models remain in the registry for backwards compatibility but users should use gpt-4o or gpt-4o-mini

**Recommended OpenAI Models:**
- `gpt-4o-mini` - Fast and cost-effective (recommended for most use cases)
- `gpt-4o` - More capable but slower and more expensive

### 2. Gemini Models
**Problem:**
- Gemini Pro and Gemini Pro Vision models were returning 404 errors
- API was using deprecated v1beta endpoint

**Solution:**
- Updated Gemini provider to use the v1 API endpoint (stable)
- Removed deprecated models (gemini-pro, gemini-pro-vision)
- Added current models:
  - `gemini-2.0-flash-exp` - Experimental 2.0 model
  - `gemini-1.5-pro` - Most capable 1.5 model
  - `gemini-1.5-flash` - Fast and efficient (recommended)
  - `gemini-1.5-flash-8b` - Smaller, faster variant

**Recommended Gemini Model:**
- `gemini-1.5-flash` - Good balance of speed and capability

### 3. Docker Backend URL Configuration
**Problem:**
- Frontend couldn't reach backend due to DNS resolution issues
- Error: "getaddrinfo ENOTFOUND backend"

**Solution:**
- Changed BACKEND_URL from `http://backend:8000` to `http://llm_backend:8000`
- This matches the actual container name defined in docker-compose.yml

## How to Use

### For OpenAI:
1. Get your API key from https://platform.openai.com/api-keys
2. Add it in the playground under "Configure API Providers" → OpenAI → "Add Key"
3. Use these models:
   - GPT-4o Mini (recommended, fast and cheap)
   - GPT-4o (more capable)
   - GPT o1 / o1-mini (reasoning models)

### For Gemini:
1. Get your API key from https://aistudio.google.com/apikey
2. Add it in the playground under "Configure API Providers" → Gemini → "Add Key"
3. Use these models:
   - Gemini 1.5 Flash (recommended)
   - Gemini 1.5 Pro (more capable)
   - Gemini 2.0 Flash Exp (experimental)

### For Claude (Anthropic):
1. Get your API key from https://console.anthropic.com/
2. Add it in the playground under "Configure API Providers" → Anthropic → "Add Key"
3. Use these models:
   - Claude 3.5 Sonnet (New) - Latest and most capable
   - Claude 3 Haiku - Fast and efficient

## Testing

To test the fixes:

```bash
cd SKYNET
docker-compose down
docker-compose build
docker-compose up
```

Then:
1. Open http://localhost:5000
2. Click "Launch Playground"
3. Add an API key for your preferred provider
4. Select a model and start chatting

## Notes

- API keys are stored encrypted in the database
- Models are automatically registered when you add an API key
- The frontend proxies all /api/* requests to the backend
- All current model names are from the official provider documentation as of January 2025
