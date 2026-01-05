#!/bin/bash
# Script to install CLIP for visual embeddings

echo "Installing CLIP for visual embeddings support..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected."
    echo "Please activate your virtual environment first:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install CLIP dependencies first
echo "📦 Installing CLIP dependencies..."
pip install ftfy regex

# Try to install CLIP from official repository
echo ""
echo "📦 Installing CLIP from OpenAI repository..."
pip install git+https://github.com/openai/CLIP.git

# Verify installation
echo ""
echo "✅ Verifying CLIP installation..."
python3 -c "import clip; import torch; print(f'✅ CLIP version: {clip.__version__ if hasattr(clip, \"__version__\") else \"installed\"}'); print(f'✅ PyTorch version: {torch.__version__}'); print('✅ CLIP is ready to use!')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 CLIP installation successful!"
    echo ""
    echo "Visual embedding support is now enabled."
    echo "The system will automatically generate visual embeddings for uploaded images."
else
    echo ""
    echo "⚠️  CLIP installation may have issues. Trying alternative method..."
    echo ""
    echo "Attempting to install clip-by-openai package..."
    pip install clip-by-openai
    
    python3 -c "import clip; print('✅ CLIP (clip-by-openai) is ready!')" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "🎉 CLIP installation successful (alternative package)!"
    else
        echo "❌ CLIP installation failed. Please install manually:"
        echo "   pip install git+https://github.com/openai/CLIP.git"
        exit 1
    fi
fi

echo ""
echo "📝 Next steps:"
echo "1. Run database migration: python manage.py migrate"
echo "2. Restart your Django server"
echo "3. Upload an image to test visual embedding generation"

