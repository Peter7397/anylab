#!/usr/bin/env python3
"""Create a simple test PDF for testing"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def create_test_pdf():
    buffer = io.BytesIO()
    
    # Create PDF
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Page 1
    c.drawString(100, height - 100, "Test PDF Document for Processing")
    c.drawString(100, height - 130, "Page 1: Introduction")
    c.drawString(100, height - 160, "This is a test document to verify PDF processing.")
    c.drawString(100, height - 190, "It contains basic text content for embedding generation.")
    
    # Page 2
    c.showPage()
    c.drawString(100, height - 100, "Page 2: Main Content")
    c.drawString(100, height - 130, "This section contains more detailed information.")
    c.drawString(100, height - 160, "Processing should extract text and create embeddings.")
    
    # Page 3
    c.showPage()
    c.drawString(100, height - 100, "Page 3: Conclusion")
    c.drawString(100, height - 130, "This test verifies the automatic processing pipeline.")
    c.drawString(100, height - 160, "Metadata extraction, chunking, and embedding generation.")
    
    c.save()
    buffer.seek(0)
    
    return buffer.getvalue()

if __name__ == '__main__':
    pdf_content = create_test_pdf()
    
    # Save to test_documents directory
    with open('../test_documents/test_processing.pdf', 'wb') as f:
        f.write(pdf_content)
    
    print("Created test_processing.pdf in test_documents/")

