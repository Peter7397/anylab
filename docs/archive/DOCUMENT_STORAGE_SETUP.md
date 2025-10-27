# Document Storage Setup Complete ✅

## Created Folder Structure

```
backend/media/documents/
├── ssb/               - SSB/KPR MHTML files
├── help_portal/       - Help portal exports (CSV/JSON)
├── pdfs/              - Product manuals and PDFs
├── products/          - Product-specific documentation
└── README.txt         - Usage instructions
```

## How to Use

### 1. SSB Files (Service Support Bulletins)
**Location:** `media/documents/ssb/`

**Steps:**
1. Export SSB page from Agilent website as MHTML
2. Save as: `M84xx.mhtml` (or any name)
3. Copy file to: `backend/media/documents/ssb/`
4. Go to UI: `http://localhost:3000/ai/knowledge/ssb`
5. Click "Import SSB File" button
6. Select the MHTML file

**Result:** 2,246+ KPRs imported and searchable

---

### 2. Help Portal Exports
**Location:** `media/documents/help_portal/`

**Steps:**
1. Export help articles as CSV/JSON
2. Copy to: `media/documents/help_portal/`
3. Use import tool (to be developed) or process via command line

**Result:** Help articles indexed in RAG

---

### 3. PDF Manuals
**Location:** `media/documents/pdfs/`

**Steps:**
1. Download manuals from product websites
2. Copy PDFs to: `media/documents/pdfs/`
3. OR upload via document manager UI

**Result:** PDFs parsed, text extracted, indexed in RAG

---

### 4. Product Documentation
**Location:** `media/documents/products/`

**For now:**
- Organize by product name
- Can create subfolders: `products/OpenLab_CDS/`, etc.

---

## File Organization Tips

### Naming Conventions:
- **SSB**: `M84xx_2025-10-27.mhtml` (include date)
- **Help Portal**: `help_export_2025-10.csv`
- **PDFs**: `ProductName_Manual_V1.2.pdf`
- **Products**: `ProductName_DocType_Date.pdf`

### Version Control:
Create dated subfolders for archiving:
```
ssb/
├── archive/
│   ├── 2025-10-01_M84xx.mhtml
│   └── 2025-09-01_M84xx.mhtml
└── current/
    └── M84xx.mhtml (latest)
```

## Current Status

✅ Folders created
✅ Ready for file upload
✅ Import button works for SSB
⏳ Help portal import tool - pending
✅ PDF upload - working via document manager

## Next Steps

1. **Copy your SSB file** to `backend/media/documents/ssb/`
2. **Copy help portal export** to `backend/media/documents/help_portal/`
3. **Copy/upload PDFs** to `backend/media/documents/pdfs/`
4. **Use import buttons** in UI to process files into RAG system

All content will be searchable via RAG! 🎉

