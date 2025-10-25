const API_BASE_URL = 'http://localhost:8000/api';
const TEST_QUERIES = [
  'What is openLab?',
  'openLab',
  'Tell me about openLab server',
  'What is openLab software?',
  'openLab server',
  'What is natural language processing?',
  'What is software quality?',
  'machine learning',
  'NLP'
];

async function testRagComparison() {
  console.log('🔍 Testing RAG Comparison...\n');
  
  // Get auth token
  const loginResponse = await fetch(`${API_BASE_URL}/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
  });
  
  if (!loginResponse.ok) {
    console.error('❌ Login failed');
    return;
  }
  
  const { access } = await loginResponse.json();
  const headers = {
    'Authorization': `Bearer ${access}`,
    'Content-Type': 'application/json'
  };
  
  for (const query of TEST_QUERIES) {
    console.log(`\n📝 Testing: "${query}"`);
    console.log('─'.repeat(50));
    
    try {
      // Test Basic RAG
      const basicResponse = await fetch(`${API_BASE_URL}/ai/rag/search/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, top_k: 8, search_mode: 'basic' })
      });
      
      const basicData = await basicResponse.json();
      
      // Test Advanced RAG
      const advancedResponse = await fetch(`${API_BASE_URL}/ai/rag/advanced/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query, top_k: 8, search_mode: 'hybrid' })
      });
      
      const advancedData = await advancedResponse.json();
      
      // Compare results
      const basicHasAnswer = !basicData.response.includes("I don't know");
      const advancedHasAnswer = !advancedData.response.includes("I don't know");
      
      console.log(`Basic RAG:  ${basicHasAnswer ? '✅' : '❌'} ${basicData.response.substring(0, 80)}...`);
      console.log(`Advanced RAG: ${advancedHasAnswer ? '✅' : '❌'} ${advancedData.response.substring(0, 80)}...`);
      
      if (basicHasAnswer && !advancedHasAnswer) {
        console.log('🚨 ISSUE FOUND: Basic RAG works but Advanced RAG fails!');
      } else if (!basicHasAnswer && advancedHasAnswer) {
        console.log('🚨 ISSUE FOUND: Advanced RAG works but Basic RAG fails!');
      } else if (basicHasAnswer && advancedHasAnswer) {
        console.log('✅ Both work correctly');
      } else {
        console.log('❌ Neither found an answer');
      }
      
      console.log(`Sources - Basic: ${basicData.sources?.length || 0}, Advanced: ${advancedData.sources?.length || 0}`);
      
    } catch (error) {
      console.error(`❌ Error testing "${query}":`, error.message);
    }
  }
}

testRagComparison().catch(console.error);
