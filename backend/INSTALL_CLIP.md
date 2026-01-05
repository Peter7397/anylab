# CLIP Installation Guide for Visual Embeddings

This guide will help you install CLIP (Contrastive Language-Image Pre-Training) for visual embedding support in Graphic RAG.

## Prerequisites

- Python 3.8 or higher
- Virtual environment activated
- PyTorch already installed (should be in requirements.txt)

## Installation Methods

### Method 1: Automated Script (Recommended)

```bash
cd backend
source venv/bin/activate  # or your virtual environment
./install_clip.sh
```

### Method 2: Manual Installation

#### Step 1: Install CLIP Dependencies

```bash
pip install ftfy regex
```

#### Step 2: Install CLIP

**Option A: From OpenAI Repository (Recommended)**
```bash
pip install git+https://github.com/openai/CLIP.git
```

**Option B: Using Alternative Package**
```bash
pip install clip-by-openai
```

### Method 3: Add to requirements.txt and Install

The dependencies (`ftfy` and `regex`) are already added to `requirements.txt`. To install CLIP:

```bash
cd backend
source venv/bin/activate
pip install git+https://github.com/openai/CLIP.git
```

## Verify Installation

Test that CLIP is working:

```python
python3 -c "import clip; import torch; print('CLIP version:', clip.__version__ if hasattr(clip, '__version__') else 'installed'); print('PyTorch version:', torch.__version__); print('✅ CLIP is ready!')"
```

## Post-Installation Steps

1. **Run Database Migration**
   ```bash
   python manage.py migrate
   ```
   This will add the `visual_embedding` field to the `DocumentChunk` model.

2. **Restart Django Server**
   ```bash
   python manage.py runserver
   ```

3. **Test Visual Embeddings**
   - Upload an image through the API
   - The system will automatically generate visual embeddings
   - Check logs for "CLIP library available for visual embeddings"

## Troubleshooting

### Issue: "No module named 'clip'"

**Solution**: Make sure CLIP is installed in the correct virtual environment:
```bash
which python  # Should point to your venv
pip install git+https://github.com/openai/CLIP.git
```

### Issue: CUDA/GPU Errors

**Solution**: CLIP will automatically use CPU if CUDA is not available. For CPU-only:
```python
# The system automatically detects and uses CPU if CUDA unavailable
# No action needed - it will work on CPU (slower but functional)
```

### Issue: "ftfy" or "regex" not found

**Solution**: Install dependencies first:
```bash
pip install ftfy regex
```

### Issue: Git not available

**Solution**: Install git or use the alternative package:
```bash
pip install clip-by-openai
```

## System Requirements

- **Memory**: CLIP models require ~500MB RAM
- **Disk**: Model files are downloaded on first use (~300MB)
- **CPU/GPU**: Works on both, GPU recommended for faster processing

## Model Information

- **Default Model**: ViT-B/32 (Vision Transformer Base, 32x32 patches)
- **Embedding Dimensions**: 512
- **Model Size**: ~150MB (downloaded automatically on first use)

## Usage

Once installed, the system will automatically:
1. Generate visual embeddings for uploaded images
2. Store embeddings in the `visual_embedding` field
3. Enable visual similarity search
4. Support hybrid text + visual queries

No additional configuration needed - it works automatically!

## Performance Notes

- **First Run**: Model download may take a few minutes
- **CPU Processing**: ~1-2 seconds per image
- **GPU Processing**: ~0.1-0.2 seconds per image
- **Caching**: Embeddings are cached for 24 hours

## Support

If you encounter issues:
1. Check that all dependencies are installed: `pip list | grep -E "(clip|torch|ftfy|regex)"`
2. Verify Python version: `python --version` (should be 3.8+)
3. Check logs for CLIP initialization messages
4. Try reinstalling: `pip uninstall clip && pip install git+https://github.com/openai/CLIP.git`

