#!/usr/bin/env python3
"""
Quick test script to verify Neo4j connection from Django
Run this from the project root: python3 test-neo4j-connection.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anylab.settings')

import django
django.setup()

from ai_assistant.services.neo4j_service import get_neo4j_service

def main():
    print("🔍 Testing Neo4j Connection...")
    print("=" * 50)
    
    # Get Neo4j service
    neo4j = get_neo4j_service()
    
    # Test connection
    print("\n1. Testing connection...")
    if neo4j.test_connection():
        print("   ✅ Connection successful!")
    else:
        print("   ❌ Connection failed!")
        return
    
    # Create constraints
    print("\n2. Creating constraints and indexes...")
    try:
        neo4j.create_constraints()
        print("   ✅ Constraints created successfully!")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")
    
    # Get graph statistics
    print("\n3. Getting graph statistics...")
    try:
        stats = neo4j.get_graph_stats()
        print(f"   📊 Total Nodes: {stats['total_nodes']}")
        print(f"   📊 Total Relationships: {stats['total_relationships']}")
        print(f"   📊 Node Labels: {len(stats['nodes'])}")
        print(f"   📊 Relationship Types: {len(stats['relationships'])}")
    except Exception as e:
        print(f"   ⚠️  Error getting stats: {e}")
    
    # Test a simple query
    print("\n4. Testing a simple query...")
    try:
        query = "RETURN 'Hello from Neo4j!' AS message, 1 + 1 AS calculation"
        result = neo4j.execute_query(query)
        if result:
            print(f"   ✅ Query successful!")
            print(f"   📝 Result: {result[0]}")
    except Exception as e:
        print(f"   ❌ Query failed: {e}")
    
    # Create a test node
    print("\n5. Creating a test node...")
    try:
        query = """
        MERGE (t:TestNode {id: 'test-001', name: 'Test Node', created: datetime()})
        RETURN t
        """
        result = neo4j.execute_query(query)
        if result:
            print("   ✅ Test node created!")
            print(f"   📝 Node: {result[0]}")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")
    
    # Verify test node exists
    print("\n6. Verifying test node...")
    try:
        query = "MATCH (t:TestNode {id: 'test-001'}) RETURN t"
        result = neo4j.execute_query(query)
        if result:
            print(f"   ✅ Test node found: {len(result)} node(s)")
        else:
            print("   ⚠️  Test node not found")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Neo4j is ready for Graph RAG implementation!")
    print("\n📚 Next Steps:")
    print("   1. Proceed with entity extraction (Week 2)")
    print("   2. Build graph from existing documents ú")
    print("   3. Implement hybrid search (Week 5)")
    print("\n📖 See GRAPH_RAG_MIGRATION_PLAN.md for details")

if __name__ == '__main__':
    main()

