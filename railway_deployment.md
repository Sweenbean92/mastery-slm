# Railway Deployment Guide

Railway is an excellent choice for this application as it supports:
- Long-running processes (Ollama can run)
- Persistent storage (ChromaDB database)
- Environment variables
- Automatic deployments from Git

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Push your code to GitHub (or use Railway's Git integration)
3. **Ollama Setup**: You'll need to install Ollama on Railway or use a service that provides Ollama

## Deployment Steps

### Option 1: Deploy via Railway Dashboard

1. **Create New Project**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or upload code)

2. **Configure Build**:
   - Railway will auto-detect Python
   - It will use the `Procfile` or `Dockerfile` if present
   - Make sure `requirements.txt` is in the root

3. **Set Environment Variables** (if needed):
   - Go to Variables tab
   - Add any required environment variables
   - Railway automatically sets `PORT` variable

4. **Deploy**:
   - Railway will automatically build and deploy
   - Check the Deployments tab for logs

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   ```

2. **Login**:
   ```bash
   railway login
   ```

3. **Initialize Project**:
   ```bash
   railway init
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

## Important Notes

### Ollama on Railway

✅ **Ollama is now included in the Dockerfile!**

The Dockerfile automatically:
- Installs Ollama during build
- Starts Ollama as a background service
- Pulls base models (phi3, smollm2, gemma3)
- Creates custom models from your Modelfiles

⚠️ **Important Considerations:**

1. **Model Download Time**: The first deployment will take longer as it downloads base models (several GB). This happens during container startup.

2. **Resource Requirements**: 
   - Railway free tier may have memory limits
   - Models require significant RAM (2-8GB+ depending on model)
   - Consider upgrading Railway plan if you hit limits

3. **Persistent Storage**: 
   - Models are stored in the container
   - Railway provides persistent volumes, but verify your plan includes them
   - Models will persist across deployments

4. **Startup Time**: 
   - First startup: 5-10 minutes (model downloads)
   - Subsequent startups: 1-2 minutes (models already cached)

5. **Memory Usage**: 
   - Monitor memory usage in Railway dashboard
   - If models don't fit, consider using smaller models or upgrading plan

### ChromaDB Storage

- ChromaDB will store data in the `chroma_db` directory
- Railway provides persistent storage, so data will persist
- Consider using ChromaDB Cloud for better reliability in production

### Environment Variables

Set these in Railway dashboard (Variables tab):
- `PORT` - Automatically set by Railway
- Any API keys if you switch to cloud LLM services
- Database connection strings if using external databases

### Static Files

- Static files in `/static` and templates in `/templates` will be included
- Make sure they're committed to Git

## Post-Deployment

1. **Check Logs**: Monitor deployment logs in Railway dashboard
   - Look for "Ollama is ready!" message
   - Check for model download progress
   - Verify "Models ready. Starting Flask app..." appears

2. **Wait for Models**: First deployment takes 5-10 minutes for model downloads
   - Don't worry if it seems stuck - models are large files
   - Check logs to see download progress

3. **Test Endpoints**: Once Flask starts, verify all routes work correctly
   - `/` - Chat interface
   - `/quiz` - Quiz interface
   - `/chat` - API endpoint
   - `/generate_question` - Quiz question generation

4. **Database**: Ensure ChromaDB is initialized with your documents
   - Documents should be in the `docs` folder
   - ChromaDB will create the database automatically

5. **Model Verification**: Test model switching in the UI
   - Try switching between phi, smoll, and gemma models
   - Verify responses are generated correctly

## Troubleshooting

- **Build Fails**: 
  - Check `requirements.txt` and ensure all dependencies are listed
  - Verify Dockerfile syntax is correct
  - Check Railway build logs for specific errors

- **App Won't Start**: 
  - Check logs for errors, verify PORT is set correctly
  - Ensure Ollama started successfully (look for "Ollama is ready!")
  - Check if models downloaded correctly

- **Ollama Not Found**: 
  - Verify Ollama installation in build logs
  - Check if `ollama serve` started successfully
  - Look for connection errors in logs

- **Models Not Loading**: 
  - Check if base models (phi3, smollm2, gemma3) were pulled
  - Verify Modelfiles are present in ModelFiles/ directory
  - Check Railway logs for model creation errors
  - Models may take 5-10 minutes to download on first run

- **Out of Memory Errors**: 
  - Railway free tier may not have enough RAM
  - Consider upgrading Railway plan
  - Or use smaller models (e.g., only phi, not all three)

- **Database Issues**: 
  - Check ChromaDB path and permissions
  - Ensure `chroma_db` directory exists and is writable
  - Verify documents are in the `docs` folder

- **Slow Responses**: 
  - First request after startup may be slow (model loading)
  - Subsequent requests should be faster
  - Check Railway resource usage

## Recommended Production Setup

For production, consider:
1. Use cloud-based LLM APIs (OpenAI, Anthropic) instead of Ollama
2. Use ChromaDB Cloud or hosted vector database
3. Set up proper error handling and logging
4. Configure CORS if needed
5. Set up monitoring and alerts

