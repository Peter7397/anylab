"""
Management command to scrape SSB database automatically.

Usage:
    python manage.py scrape_ssb
    python manage.py scrape_ssb --help-portal
    python manage.py scrape_ssb --max-pages 50
    python manage.py scrape_ssb --full
"""

import logging
import json
import requests
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from ai_assistant.ssb_scraper import SSBScraper, SSBProcessor, ScrapingConfig
from ai_assistant.models import DocumentFile
from ai_assistant.kpr_index_parser import KPRIndexParser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape Service Support Bulletin (SSB) database from Agilent'

    def add_arguments(self, parser):
        parser.add_argument(
            '--help-portal',
            action='store_true',
            help='Scrape OpenLab Help Portal instead of SSB database',
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=100,
            help='Maximum number of pages to scrape (default: 100)',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Perform full scrape of both SSB and Help Portal',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=None,
            help='Only scrape entries newer than N days',
        )
        parser.add_argument(
            '--parse-index',
            action='store_true',
            help='Parse KPR index page instead of individual pages',
        )
        parser.add_argument(
            '--index-url',
            type=str,
            default=None,
            help='URL to KPR index page',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(self.style.SUCCESS(
            f'Starting SSB scraping at {start_time}'
        ))
        
        # Check if parsing index
        if options.get('parse_index', False):
            return self._parse_kpr_index(options)
        
        # Get scraping configuration
        config = ScrapingConfig(
            max_pages=options.get('max_pages', 100),
            delay_between_requests=1.0,
            timeout=30,
            retry_attempts=3
        )
        
        try:
            scraper = SSBScraper(config)
            processor = SSBProcessor()
            
            results = {
                'ssb_database': {'scraped': 0, 'processed': 0, 'new': 0, 'updated': 0},
                'help_portal': {'scraped': 0, 'processed': 0, 'new': 0, 'updated': 0}
            }
            
            # Check if we should scrape SSB database
            if not options.get('help_portal', False) or options.get('full', False):
                self.stdout.write(self.style.WARNING('Scraping SSB database...'))
                
                ssb_entries = scraper.scrape_all_ssbs()
                results['ssb_database']['scraped'] = len(ssb_entries)
                
                if ssb_entries:
                    # Process entries
                    processing_results = processor.process_ssb_entries(ssb_entries)
                    results['ssb_database']['processed'] = processing_results.get('processed', 0)
                    results['ssb_database']['new'] = processing_results.get('created', 0)
                    results['ssb_database']['updated'] = processing_results.get('updated', 0)
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'SSB Database: Scraped {len(ssb_entries)}, '
                        f'Processed {processing_results.get("processed", 0)}, '
                        f'New {processing_results.get("created", 0)}, '
                        f'Updated {processing_results.get("updated", 0)}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING('No SSB entries found'))
            
            # Check if we should scrape Help Portal
            if options.get('help_portal', False) or options.get('full', False):
                self.stdout.write(self.style.WARNING('Scraping OpenLab Help Portal...'))
                
                help_entries = scraper.scrape_openlab_help_portal()
                results['help_portal']['scraped'] = len(help_entries)
                
                if help_entries:
                    # Process help entries
                    processed_count = 0
                    for entry in help_entries:
                        try:
                            # Check if already exists
                            existing_doc = DocumentFile.objects.filter(
                                title=entry['title']
                            ).first()
                            
                            if existing_doc:
                                results['help_portal']['updated'] += 1
                            else:
                                results['help_portal']['new'] += 1
                            
                            processed_count += 1
                        except Exception as e:
                            logger.error(f"Error processing help entry: {e}")
                            continue
                    
                    results['help_portal']['processed'] = processed_count
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'Help Portal: Scraped {len(help_entries)}, '
                        f'Processed {processed_count}, '
                        f'New {results["help_portal"]["new"]}, '
                        f'Updated {results["help_portal"]["updated"]}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING('No Help Portal entries found'))
            
            # Summary
            end_time = timezone.now()
            duration = end_time - start_time
            
            total_new = results['ssb_database']['new'] + results['help_portal']['new']
            total_updated = results['ssb_database']['updated'] + results['help_portal']['updated']
            
            self.stdout.write(self.style.SUCCESS(
                f'\nScraping completed in {duration.total_seconds():.2f} seconds\n'
                f'Total New Entries: {total_new}\n'
                f'Total Updated Entries: {total_updated}\n'
                f'Completed at {end_time}'
            ))
            
        except Exception as e:
            logger.error(f"Error during SSB scraping: {e}", exc_info=True)
            raise CommandError(f'SSB scraping failed: {e}')
    
    def _parse_kpr_index(self, options):
        """Parse KPR index page and import entries"""
        try:
            self.stdout.write(self.style.WARNING('Parsing KPR index page...'))
            
            # Initialize parser
            parser = KPRIndexParser()
            
            # Fetch index page
            index_url = options.get('index_url') or 'https://www.agilent.com/cs/library/support/Patches/SSBs/M84xx.html'
            
            self.stdout.write(f'Fetching index from: {index_url}')
            
            try:
                # Handle local files
                if index_url.startswith('file://'):
                    file_path = index_url.replace('file://', '')
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    self.stdout.write(f'Loaded index from local file: {file_path}')
                else:
                    # Fetch from URL
                    response = requests.get(index_url, timeout=30)
                    response.raise_for_status()
                    html_content = response.text
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to fetch index page: {e}'))
                self.stdout.write(self.style.WARNING('\nTo use a local file, save the index page as HTML and run:'))
                self.stdout.write('python manage.py scrape_ssb --parse-index --index-url file:///full/path/to/file.html')
                return
            
            # Parse the index
            kpr_entries = parser.get_recent_kprs(html_content, months=3)
            
            if not kpr_entries:
                self.stdout.write(self.style.WARNING('No KPR entries found in index'))
                return
            
            self.stdout.write(f'Found {len(kpr_entries)} KPR entries')
            
            # Import entries into database
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            for i, kpr_entry in enumerate(kpr_entries):
                try:
                    # Fetch full details for all KPRs
                    metadata = parser.extract_kpr_metadata(kpr_entry, fetch_full_details=True)
                    
                    # Check if KPR already exists
                    existing = DocumentFile.objects.filter(
                        document_type='SSB_KPR',
                        metadata__kpr_number=kpr_entry['kpr_number']
                    ).first()
                    
                    if existing:
                        # Update existing
                        existing.title = metadata['title']
                        existing.description = metadata['description']
                        existing.metadata = json.dumps(metadata)
                        existing.save()
                        updated_count += 1
                        self.stdout.write(f'Updated KPR#{kpr_entry["kpr_number"]}')
                    else:
                        # Create new
                        DocumentFile.objects.create(
                            title=metadata['title'],
                            filename=f"KPR_{kpr_entry['kpr_number']}.txt",
                            document_type='SSB_KPR',
                            description=metadata['description'],
                            metadata=json.dumps(metadata),
                            page_count=1,
                            file_size=len(metadata['title'])
                        )
                        imported_count += 1
                        self.stdout.write(f'Imported KPR#{kpr_entry["kpr_number"]}')
                    
                except Exception as e:
                    logger.error(f"Error importing KPR {kpr_entry.get('kpr_number')}: {e}")
                    skipped_count += 1
                    continue
            
            # Summary
            self.stdout.write(self.style.SUCCESS(
                f'\nKPR Import Summary:\n'
                f'Total Parsed: {len(kpr_entries)}\n'
                f'Imported: {imported_count}\n'
                f'Updated: {updated_count}\n'
                f'Skipped: {skipped_count}\n'
            ))
            
        except Exception as e:
            logger.error(f"Error parsing KPR index: {e}", exc_info=True)
            raise CommandError(f'KPR index parsing failed: {e}')


