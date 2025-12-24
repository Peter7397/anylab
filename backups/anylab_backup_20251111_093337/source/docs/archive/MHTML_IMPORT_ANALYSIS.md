# MHTML Import Analysis - Findings

## Problem Summary
The M84xx.mhtml file contains **2,246 KPR entries**, but the parser was only extracting **34 KPRs**.

## Root Cause Analysis

### File Format
- **File**: `/Users/pinggenchen/Downloads/M84xx.mhtml` (2.0MB)
- **Encoding**: MIME Quoted-Printable (CRLF line endings)
- **Structure**: HTML wrapped in MIME boundaries

### Extraction Issues

1. **MIME Encoding**: The file uses Quoted-Printable encoding:
   - `=` is encoded as `=3D`
   - Spaces are encoded as `=20`
   - Newlines as `=0D=0A`
   - **Solution**: Using Python's `quopri.decodestring()` module

2. **Text Splitting**: The `_extract_kprs_by_keyword()` method splits text by `\n`:
   - Multi-line KPR descriptions get split across lines
   - Pattern matching fails because full description isn't on one line
   - **Example**: 
     ```
     Line 1: "KPR#:147"
     Line 2: "  6890N with 7693 barcode scanning checksum mismatch"
     Line 3: "  does not return vial to tray and skips a vial."
     ```
   - **Solution**: Parse as multi-line entries instead of line-by-line

3. **Pattern Matching**: Current regex only matches single line:
   - Pattern: `r'KPR#:\s*(\d+)(.*?)'`
   - Only captures text on the same line
   - **Solution**: Use a multi-line regex with `re.DOTALL`

## Statistics
- Total KPR entries in file: **2,246**
- Currently extracted: **34** (1.5% success rate)
- Keywords detected: **50+**
- Format: Keyword sections with KPR entries

## Proposed Solution

### Update Parser Logic
Instead of line-by-line parsing, use a multi-line approach:

```python
def _extract_kprs_by_keyword(self, text: str) -> Dict[str, List[Dict]]:
    # Split by keywords
    keyword_sections = re.split(r'Keyword:\s*([^\n]+)', text)
    
    # Process each section
    for section in keyword_sections:
        if section.startswith('Keyword:'):
            current_keyword = re.sub(r'Keyword:\s*', '', section).strip()
            kpr_by_keyword[current_keyword] = []
        else:
            # Extract all KPRs from this section (multi-line)
            kpr_matches = re.finditer(
                r'KPR#:\s*(\d+)(.*?)(?=KPR#:|$)', 
                section, 
                re.DOTALL
            )
            for match in kpr_matches:
                kpr_num = match.group(1)
                title = match.group(2).strip()
                # ... create entry
```

## Current Status
- ✅ MIME decoding fixed
- ✅ HTML extraction working  
- ✅ KPR pattern detection confirmed (2,246 found)
- ❌ Text parsing only catching 34 entries due to line-by-line approach
- ❌ Need multi-line KPR extraction

## Next Steps
1. Rewrite `_extract_kprs_by_keyword()` to handle multi-line entries
2. Test with the MHTML file
3. Verify all 2,246 KPRs are extracted correctly
4. Re-test import functionality in UI

