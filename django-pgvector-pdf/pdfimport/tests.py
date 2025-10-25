from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document
import io

class PDFImportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_login_required(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_upload_pdf(self):
        self.client.login(username='testuser', password='testpass')
        pdf_content = b'%PDF-1.4 test pdf content'  # Minimal PDF header
        pdf_file = SimpleUploadedFile('test.pdf', pdf_content, content_type='application/pdf')
        response = self.client.post(reverse('upload'), {'pdf': pdf_file})
        self.assertContains(response, 'PDF uploaded!', status_code=200)
        self.assertEqual(Document.objects.count(), 1)

    def test_query_vector(self):
        self.client.login(username='testuser', password='testpass')
        # Add a document manually
        Document.objects.create(content='test content', embedding=[0.0]*384)
        response = self.client.post(reverse('query'), {'query': 'test'})
        self.assertContains(response, 'test content') 