from django.core.management.base import BaseCommand
from django.db import transaction
from ai_assistant.models import UploadedFile, DocumentChunk
import re

class Command(BaseCommand):
    help = "Add glossary micro-chunks (definition/acronym snippets) to existing documents. Non-destructive."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100000, help='Max files to process')
        parser.add_argument('--dry-run', action='store_true', help='Analyze only, no writes')

    def handle(self, *args, **options):
        limit = options['limit']
        dry = options['dry_run']

        files_qs = UploadedFile.objects.filter(chunks_created=True).order_by('id')[:limit]
        total_files = files_qs.count()
        created = 0

        self.stdout.write(self.style.NOTICE(f"Processing {total_files} files (limit={limit})"))

        # Simple self-contained extractors
        def extract_microchunks(text: str):
            text = re.sub(r"\s+", " ", text or '').strip()
            if not text:
                return []
            snippets = []
            # Definition-like: "Term is ... ."
            pattern_def = re.compile(r"\b([A-Z][A-Za-z0-9_\-/]{1,50})\b\s+(is|are)\s+[^.]{10,200}\.")
            for m in pattern_def.finditer(text):
                s, e = m.start(), m.end()
                snippet = text[max(0, s-20):min(len(text), e+20)]
                if 80 <= len(snippet) <= 200:
                    snippets.append(snippet.strip())
            # Acronyms: ALL CAPS 2-5 chars, take surrounding window
            for m in re.finditer(r"\b([A-Z]{2,5})\b", text[:1200]):
                s, e = m.start(), m.end()
                snippet = text[max(0, s-60):min(len(text), e+120)]
                if 60 <= len(snippet) <= 180:
                    snippets.append(snippet.strip())
            # De-dup similar snippets
            uniq = []
            seen = set()
            for sn in snippets:
                key = sn.lower()[:120]
                if key not in seen:
                    seen.add(key)
                    uniq.append(sn)
            return uniq

        with transaction.atomic():
            for idx, uf in enumerate(files_qs, 1):
                chunks = DocumentChunk.objects.filter(uploaded_file=uf).order_by('page_number', 'chunk_index')
                pages = {}
                for ch in chunks:
                    pages.setdefault(ch.page_number or 1, []).append(ch.content or '')
                added_for_file = 0
                for page_num, parts in pages.items():
                    text = " \n".join(parts)
                    micros = extract_microchunks(text)
                    for snip in micros[:20]:  # cap per page to avoid explosion
                        if not dry:
                            DocumentChunk.objects.create(
                                uploaded_file=uf,
                                content=snip,
                                embedding=None,
                                page_number=page_num,
                                chunk_index=999999
                            )
                        added_for_file += 1
                        created += 1
                self.stdout.write(f"[{idx}/{total_files}] {uf.id} -> +{added_for_file}")

        self.stdout.write(self.style.SUCCESS(f"Created {created} glossary micro-chunks"))
