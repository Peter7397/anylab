// Frontend Interface Test Script
// This script simulates the frontend API calls to test the complete functionality

const API_BASE_URL = 'http://localhost:8000/api';
const TEST_CREDENTIALS = {
    username: 'admin',
    password: 'admin123'
};

class FrontendTester {
    constructor() {
        this.token = null;
        this.testResults = [];
    }

    async log(message, type = 'info') {
        const timestamp = new Date().toISOString();
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
        this.testResults.push({ timestamp, type, message });
    }

    async authenticate() {
        try {
            const response = await fetch(`${API_BASE_URL}/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(TEST_CREDENTIALS)
            });

            if (!response.ok) {
                throw new Error(`Authentication failed: ${response.status}`);
            }

            const data = await response.json();
            this.token = data.access;
            await this.log('Authentication successful', 'success');
            return true;
        } catch (error) {
            await this.log(`Authentication failed: ${error.message}`, 'error');
            return false;
        }
    }

    async testDocumentListing() {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/documents/`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Document listing failed: ${response.status}`);
            }

            const documents = await response.json();
            await this.log(`Document listing successful - Found ${documents.length} documents`, 'success');
            
            documents.forEach(doc => {
                this.log(`  - ${doc.title} (${doc.document_type}) - ${doc.file_size_mb}`, 'info');
            });

            return documents;
        } catch (error) {
            await this.log(`Document listing failed: ${error.message}`, 'error');
            return [];
        }
    }

    async testDocumentSearch(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/documents/search/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    search_type: 'both',
                    document_type: 'all'
                })
            });

            if (!response.ok) {
                throw new Error(`Document search failed: ${response.status}`);
            }

            const results = await response.json();
            await this.log(`Document search for "${query}" successful - Found ${results.length} results`, 'success');
            return results;
        } catch (error) {
            await this.log(`Document search failed: ${error.message}`, 'error');
            return [];
        }
    }

    async testRagSearch(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/rag/search/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 5,
                    search_mode: 'comprehensive'
                })
            });

            if (!response.ok) {
                throw new Error(`RAG search failed: ${response.status}`);
            }

            const result = await response.json();
            await this.log(`RAG search for "${query}" successful`, 'success');
            await this.log(`Response: ${result.response.substring(0, 100)}...`, 'info');
            return result;
        } catch (error) {
            await this.log(`RAG search failed: ${error.message}`, 'error');
            return null;
        }
    }

    async testAdvancedRagSearch(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/rag/advanced/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 5,
                    search_mode: 'hybrid'
                })
            });

            if (!response.ok) {
                throw new Error(`Advanced RAG search failed: ${response.status}`);
            }

            const result = await response.json();
            await this.log(`Advanced RAG search for "${query}" successful`, 'success');
            await this.log(`Response: ${result.response.substring(0, 100)}...`, 'info');
            return result;
        } catch (error) {
            await this.log(`Advanced RAG search failed: ${error.message}`, 'error');
            return null;
        }
    }

    async testComprehensiveRagSearch(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/rag/comprehensive/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 10,
                    include_stats: true
                })
            });

            if (!response.ok) {
                throw new Error(`Comprehensive RAG search failed: ${response.status}`);
            }

            const result = await response.json();
            await this.log(`Comprehensive RAG search for "${query}" successful`, 'success');
            await this.log(`Response: ${result.response.substring(0, 100)}...`, 'info');
            return result;
        } catch (error) {
            await this.log(`Comprehensive RAG search failed: ${error.message}`, 'error');
            return null;
        }
    }

    async testVectorSearch(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/ai/vector/search/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: query,
                    top_k: 3
                })
            });

            if (!response.ok) {
                throw new Error(`Vector search failed: ${response.status}`);
            }

            const result = await response.json();
            await this.log(`Vector search for "${query}" successful - Found ${result.results.length} results`, 'success');
            
            result.results.forEach((item, index) => {
                this.log(`  Result ${index + 1}: Similarity ${item.similarity.toFixed(3)} - ${item.content.substring(0, 50)}...`, 'info');
            });

            return result;
        } catch (error) {
            await this.log(`Vector search failed: ${error.message}`, 'error');
            return null;
        }
    }

    async testDocumentUpload(fileContent, title, description) {
        try {
            const formData = new FormData();
            const blob = new Blob([fileContent], { type: 'text/plain' });
            formData.append('file', blob, 'test_document.txt');
            formData.append('title', title);
            formData.append('description', description);

            const response = await fetch(`${API_BASE_URL}/ai/documents/upload/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Document upload failed: ${errorData.error || response.status}`);
            }

            const result = await response.json();
            await this.log(`Document upload successful - ID: ${result.id}, Title: ${result.title}`, 'success');
            return result;
        } catch (error) {
            await this.log(`Document upload failed: ${error.message}`, 'error');
            return null;
        }
    }

    async runAllTests() {
        await this.log('Starting Frontend Interface Tests', 'info');
        await this.log('================================', 'info');

        // Test 1: Authentication
        const authSuccess = await this.authenticate();
        if (!authSuccess) {
            await this.log('Cannot proceed without authentication', 'error');
            return;
        }

        // Test 2: Document Listing
        await this.log('', 'info');
        await this.log('Test 2: Document Listing', 'info');
        await this.log('----------------------', 'info');
        const documents = await this.testDocumentListing();

        // Test 3: Document Search
        await this.log('', 'info');
        await this.log('Test 3: Document Search', 'info');
        await this.log('---------------------', 'info');
        await this.testDocumentSearch('NLP');
        await this.testDocumentSearch('software');

        // Test 4: RAG Search
        await this.log('', 'info');
        await this.log('Test 4: RAG Search', 'info');
        await this.log('----------------', 'info');
        await this.testRagSearch('What is natural language processing?');
        await this.testRagSearch('What is software quality?');

        // Test 4.5: Advanced RAG Search
        await this.log('', 'info');
        await this.log('Test 4.5: Advanced RAG Search', 'info');
        await this.log('---------------------------', 'info');
        await this.testAdvancedRagSearch('What is machine learning?');
        await this.testAdvancedRagSearch('What is software quality?');

        // Test 4.6: Comprehensive RAG Search
        await this.log('', 'info');
        await this.log('Test 4.6: Comprehensive RAG Search', 'info');
        await this.log('--------------------------------', 'info');
        await this.testComprehensiveRagSearch('What is natural language processing?');
        await this.testComprehensiveRagSearch('What is software quality?');

        // Test 5: Vector Search
        await this.log('', 'info');
        await this.log('Test 5: Vector Search', 'info');
        await this.log('-------------------', 'info');
        await this.testVectorSearch('machine learning');
        await this.testVectorSearch('software quality standards');

        // Test 6: Document Upload
        await this.log('', 'info');
        await this.log('Test 6: Document Upload', 'info');
        await this.log('----------------------', 'info');
        const testContent = 'This is a test document for frontend interface testing. It contains information about frontend development, React components, and user interface design.';
        await this.testDocumentUpload(testContent, 'Frontend Test Document', 'Test document for frontend interface validation');

        // Summary
        await this.log('', 'info');
        await this.log('Test Summary', 'info');
        await this.log('============', 'info');
        const successCount = this.testResults.filter(r => r.type === 'success').length;
        const errorCount = this.testResults.filter(r => r.type === 'error').length;
        await this.log(`Total tests: ${this.testResults.length}`, 'info');
        await this.log(`Successful: ${successCount}`, 'success');
        await this.log(`Errors: ${errorCount}`, errorCount > 0 ? 'error' : 'success');
        
        if (errorCount === 0) {
            await this.log('🎉 All frontend interface tests passed!', 'success');
        } else {
            await this.log('❌ Some tests failed. Check the logs above.', 'error');
        }
    }
}

// Run the tests
const tester = new FrontendTester();
tester.runAllTests().catch(console.error);
