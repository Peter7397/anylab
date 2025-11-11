# Fix psycopg2-binary Installation Issue

## The Problem

You're getting this error:
```
Error: pg_config executable not found.
```

This happens because `psycopg2-binary` needs PostgreSQL development headers to build.

## Solution 1: Install PostgreSQL via Homebrew (Recommended)

On macOS, install PostgreSQL which includes `pg_config`:

```bash
# Install Homebrew if you don't have it
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL (includes pg_config)
brew install postgresql@15

# Add pg_config to PATH (add to ~/.zshrc for permanent)
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Or if using Intel Mac:
# export PATH="/usr/local/opt/postgresql@15/bin:$PATH"

# Reload shell
source ~/.zshrc

# Verify pg_config is available
which pg_config
```

Then try installing again:
```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
pip install -r requirements.txt
```

## Solution 2: Install Full PostgreSQL (Not Needed for Docker Users)

**Only use this if Solution 1 doesn't work:**

```bash
# Install full PostgreSQL (includes pg_config)
brew install postgresql@15
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
# Or for Intel Mac: export PATH="/usr/local/opt/postgresql@15/bin:$PATH"
```

**Note:** Since you're using Docker for PostgreSQL, you don't need this. Use Solution 1 instead.

## Solution 3: Use Pre-built Wheel (Quick Fix)

Try installing psycopg2-binary separately with a pre-built wheel:

```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Try installing psycopg2-binary with no-cache
pip install --no-cache-dir psycopg2-binary==2.9.10

# If that fails, try without version pinning
pip install --no-cache-dir psycopg2-binary

# Then install rest of requirements
pip install -r requirements.txt
```

## Solution 4: Skip psycopg2 for Now (If Using Docker)

If you're using Docker for PostgreSQL and don't need local psycopg2:

```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate

# Install everything except psycopg2-binary
pip install -r requirements.txt --ignore-installed psycopg2-binary

# Or manually install other packages
pip install Django==5.2.4 djangorestframework==3.16.0 django-cors-headers==4.7.0
# ... etc (install other packages from requirements.txt)
```

**Note:** You'll still need psycopg2-binary to connect to PostgreSQL, so this is only temporary.

## Solution 5: Use psycopg (Newer Alternative)

The newer `psycopg` package (version 3) might work better:

```bash
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate

# Install psycopg instead of psycopg2-binary
pip install psycopg[binary]

# Then install rest of requirements (might need to comment out psycopg2-binary in requirements.txt)
```

**Note:** This requires updating Django settings if you switch from psycopg2 to psycopg.

## Recommended: Quick Fix (For Docker PostgreSQL Users)

Since you're using PostgreSQL from Docker, install only the client libraries:

```bash
# Install libpq (PostgreSQL client library only - lightweight!)
brew install libpq

# Add to PATH (for this session)
export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
# Or for Intel Mac: export PATH="/usr/local/opt/libpq/bin:$PATH"

# Verify
which pg_config

# Now install requirements
cd /Volumes/Orico/Anylab103/backend
source venv/bin/activate
pip install -r requirements.txt
```

**This is much lighter than installing the full PostgreSQL server!**

## After Fixing

Once psycopg2-binary installs successfully, you can continue with GraphRAG reprocessing:

```bash
# Verify installation worked
python manage.py check_pdf_status

# Then proceed with reprocessing
python manage.py reprocess_graph_rag --document-id 1
```

