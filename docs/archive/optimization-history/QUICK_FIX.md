# Quick Fix: Activate Virtual Environment

You're getting the error because the virtual environment isn't activated. Here's how to fix it:

## The Problem

```
ImportError: Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?
```

## The Solution

**Activate the virtual environment first!**

```bash
# 1. Go to backend directory
cd /Volumes/Orico/Anylab103/backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. You should see (venv) in your prompt
# Example: (venv) pinggenchen@PeterMac backend %
```

## Then Run Your Commands

After activation, you can run:

```bash
# Check document status
python3 manage.py check_pdf_status

# Or use python (should work after activation)
python manage.py check_pdf_status

# Reprocess documents
python manage.py reprocess_graph_rag --document-id 1
```

## How to Know It's Activated

You'll see `(venv)` at the start of your terminal prompt:

```
(venv) pinggenchen@PeterMac backend %
```

## If Virtual Environment Doesn't Exist

If you get an error that `venv` doesn't exist, create it:

```bash
cd /Volumes/Orico/Anylab103/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Reference

**Every time you open a new terminal:**
1. `cd /Volumes/Orico/Anylab103/backend`
2. `source venv/bin/activate`
3. Then run your commands

**To deactivate (when done):**
```bash
deactivate
```

---

**Now try again:**
```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
python manage.py check_pdf_status
```

