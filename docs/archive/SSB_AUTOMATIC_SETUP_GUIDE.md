# SSB Automatic Scraping Setup Guide

This guide explains how to set up automatic weekly scraping of Service Support Bulletins (SSB) from Agilent's website.

## How It Works

### 1. **Scraping Process**
The system scrapes the SSB database from:
- **Primary Source**: `https://www.agilent.com/cs/library/support/Patches/SSBs/M84xx.html`
- **Help Portal**: `https://openlab.help.agilent.com/en/index.htm`

### 2. **What Gets Extracted**
- KPR (Known Problem Report) numbers
- Title and description
- Severity level (Critical/High/Medium/Low/Informational)
- Software platform and version
- Affected components
- Symptoms
- Root cause
- Solution and workaround
- Prerequisites and risks
- Rollback procedures
- Related KPRs
- Dates (created/updated)

### 3. **Data Storage**
All SSB entries are stored in the `DocumentFile` model with:
- Document type: `SSB_KPR`
- Full metadata in JSON format
- Content chunks for RAG search
- Source URLs for reference

## Setup Options

### Option 1: Manual Scraping (Recommended for Testing)

Run the management command manually:

```bash
cd backend
python manage.py scrape_ssb
```

**Options:**
```bash
# Scrape SSB database (default)
python manage.py scrape_ssb

# Scrape help portal instead
python manage.py scrape_ssb --help-portal

# Scrape both
python manage.py scrape_ssb --full

# Limit number of pages
python manage.py scrape_ssb --max-pages 50

# Only recent entries (last 7 days)
python manage.py scrape_ssb --days-back 7
```

### Option 2: Automated Weekly Scraping with Cron (Linux/Mac)

Add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 cd /path/to/OnLab0812/backend && /path/to/venv/bin/python manage.py scrape_ssb --full
```

### Option 3: Automated Scraping with Celery (Recommended for Production)

Create a Celery periodic task:

```python
# backend/ai_assistant/tasks.py (create if doesn't exist)

from celery import shared_task
from django.core.management import call_command

@shared_task
def scrape_ssb_weekly():
    """Automatically scrape SSB database every week"""
    try:
        call_command('scrape_ssb', '--full', verbosity=0)
        logger.info('Weekly SSB scraping completed successfully')
    except Exception as e:
        logger.error(f'SSB scraping failed: {e}')
        raise
```

Add to `backend/anylab/celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape-ssb-weekly': {
        'task': 'ai_assistant.tasks.scrape_ssb_weekly',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Every Sunday at 2 AM
    },
}
```

### Option 4: Windows Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Weekly on Sunday at 2:00 AM
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `manage.py scrape_ssb --full`
   - Start in: `C:\path\to\OnLab0812\backend`

## UI Features

### Automatic Recognition
The SSB Database UI automatically displays:

1. **New This Week** - SSBs added in the last 7 days
   - Green pulsing indicator
   - Compact card view
   - Automatically shows at page load

2. **New This Month** - SSBs added in the last 30 days
   - Blue indicator
   - Up to 10 entries shown
   - Compact card view

3. **All SSB Entries** - Full list with search and filters
   - Search by KPR, title, platform, symptoms, solution
   - Filter by severity, status, platform
   - Export to CSV

## How to Verify It's Working

1. **Check Backend Logs**
   ```bash
   tail -f backend/logs/anylab.log
   ```

2. **View in Django Admin**
   - Go to Django Admin → Document Files
   - Filter by `document_type = SSB_KPR`
   - Check `created_at` dates

3. **Check in UI**
   - Navigate to `http://localhost:3000/ai/knowledge/ssb`
   - Look for "New This Week" and "New This Month" sections
   - Entries should appear with recent `created_date`

## Troubleshooting

### Issue: Scraper not running
**Solution**: Check Celery is running
```bash
celery -A anylab worker --loglevel=info
celery -A anylab beat --loglevel=info
```

### Issue: No new SSBs appearing
**Solution**: 
1. Check if website structure changed
2. Verify URLs are accessible
3. Check network connectivity
4. Run manual scrape to test: `python manage.py scrape_ssb --max-pages 5`

### Issue: Duplicate entries
**Solution**: The system automatically prevents duplicates using KPR number matching

### Issue: Slow scraping
**Solution**: Adjust `delay_between_requests` in `ScrapingConfig` or limit pages with `--max-pages`

## Configuration

Edit `backend/ai_assistant/ssb_scraper.py` to customize:

```python
@dataclass
class ScrapingConfig:
    base_url: str = "..."  # Change source URL
    max_pages: int = 100    # Limit pages scraped
    delay_between_requests: float = 1.0  # Rate limiting
    timeout: int = 30       # Request timeout
    retry_attempts: int = 3 # Retry on failure
```

## Next Steps

1. Run initial scrape: `python manage.py scrape_ssb --full`
2. Check UI at `http://localhost:3000/ai/knowledge/ssb`
3. Set up automated scheduling (cron or Celery)
4. Monitor logs weekly to ensure it's working
5. Update scraper if Agilent changes their website structure

## Summary

✅ **Backend**: Fully implemented scraper with API endpoints  
✅ **Management Command**: `python manage.py scrape_ssb`  
✅ **Frontend UI**: Shows new entries automatically by date  
✅ **Automation**: Set up with cron or Celery  

The system will automatically scrape new SSBs from Agilent's website, store them in your database, and display them in the "New This Week" and "New This Month" sections!

