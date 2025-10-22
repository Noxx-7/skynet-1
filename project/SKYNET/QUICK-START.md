# SKYNET Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- An API key from OpenAI, Anthropic, or Google Gemini

## Step 1: Start the application

```bash
cd SKYNET
docker compose down
docker compose build --no-cache
docker compose up
```

Wait for all services to be ready. You should see:
```
postgres_db  | database system is ready to accept connections
llm_backend  | INFO:     Application startup complete.
llm_frontend | ready started server on 0.0.0.0:5000
```

## Step 2: Open the playground

Open your browser and navigate to:
```
http://localhost:5000/playground
```

## Step 3: Add your API key

In the left sidebar, find "Configure API Providers" section:

### For OpenAI:
1. Click "Add Key" next to "openai"
2. Enter your OpenAI API key (starts with `sk-`)
3. Click OK

### For Anthropic (Claude):
1. Click "Add Key" next to "anthropic"
2. Enter your Anthropic API key
3. Click OK

### For Google Gemini:
1. Click "Add Key" next to "gemini"
2. Enter your Google AI API key
3. Click OK

## Step 4: Select a model

After adding an API key:
- Models will automatically appear in the "Models" section
- Click on any model to select it
- Examples:
  - **OpenAI**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
  - **Anthropic**: Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
  - **Gemini**: Gemini Pro, Gemini Pro Vision

## Step 5: Start chatting!

1. Type your message in the text box at the bottom
2. Press Enter or click the "Send" button
3. Wait for the model's response

## Features Available

### Main Features:
- **Multiple LLM providers**: OpenAI, Anthropic, Google Gemini
- **Model switching**: Change models and chat history clears automatically
- **Settings**: Adjust temperature and max tokens
- **Message history**: See your conversation with each model

### Additional Pages:
- **Home**: `http://localhost:5000/`
- **Code Editor**: `http://localhost:5000/code-editor`
- **Playground**: `http://localhost:5000/playground`

## Troubleshooting

### No models showing?
1. Check browser console (F12) for errors
2. Verify API key was added successfully (button should say "Update Key")
3. Refresh the page
4. See TROUBLESHOOTING.md for detailed debugging

### Backend not responding?
```bash
# Check if backend is running
docker compose ps

# View backend logs
docker compose logs backend --tail 50

# Restart backend only
docker compose restart backend
```

### Clear everything and start fresh?
```bash
docker compose down -v  # This removes volumes too
docker compose build --no-cache
docker compose up
```

## Getting API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API keys section
4. Create a new secret key
5. Copy the key (starts with `sk-`)

### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API keys
4. Create a new key
5. Copy the key

### Google Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Create a new API key
4. Copy the key

## Architecture

```
┌─────────────────────────────────────────┐
│         Browser (port 5000)             │
│    http://localhost:5000/playground     │
└──────────────┬──────────────────────────┘
               │
               │ HTTP Requests
               ↓
┌─────────────────────────────────────────┐
│     Next.js Frontend (port 5000)        │
│     Proxies /api/* to backend           │
└──────────────┬──────────────────────────┘
               │
               │ API Calls
               ↓
┌─────────────────────────────────────────┐
│     FastAPI Backend (port 8000)         │
│     - Manages API keys (encrypted)      │
│     - Calls LLM providers               │
│     - Auto-registers models             │
└──────────────┬──────────────────────────┘
               │
               │ Database Queries
               ↓
┌─────────────────────────────────────────┐
│     PostgreSQL (port 5432)              │
│     - Stores API keys (encrypted)       │
│     - Stores model metadata             │
└─────────────────────────────────────────┘
```

## Security Notes

- API keys are encrypted before storage
- Keys are stored in PostgreSQL database
- No authentication required for demo (single-user mode)
- For production use, enable authentication

## Next Steps

Once you're comfortable with the playground:
1. Explore the **Code Editor** for writing and testing code
2. Try different models and compare responses
3. Adjust temperature and max tokens in Settings
4. Upload custom models (experimental)

Need help? Check TROUBLESHOOTING.md for detailed debugging information.
