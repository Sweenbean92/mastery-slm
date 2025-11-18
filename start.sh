#!/bin/bash

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 5

# Check if Ollama is running
until curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama API..."
    sleep 2
done

echo "Ollama is ready!"

# Pull base models first, then create custom models
echo "Setting up models..."
if [ -f "ModelFiles/Phi3_ModelFile" ]; then
    echo "Pulling base phi3 model..."
    ollama pull phi3 || true
    echo "Creating custom phi model..."
    ollama create phi -f ModelFiles/Phi3_ModelFile || true
fi
if [ -f "ModelFiles/SmolLLM2_Modelfile" ]; then
    echo "Pulling base smollm2 model..."
    ollama pull smollm2 || true
    echo "Creating custom smoll model..."
    ollama create smoll -f ModelFiles/SmolLLM2_Modelfile || true
fi
if [ -f "ModelFiles/Gemma3_ModelFile" ]; then
    echo "Pulling base gemma3 model..."
    ollama pull gemma3 || true
    echo "Creating custom gemma model..."
    ollama create gemma -f ModelFiles/Gemma3_ModelFile || true
fi

echo "Models ready. Starting Flask app..."

# Start Flask app in foreground
exec python app.py

