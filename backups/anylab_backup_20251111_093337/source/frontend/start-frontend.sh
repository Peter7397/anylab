#!/bin/bash

# AnyLab Frontend Startup Script
# Simple script to start the React development server

echo "🚀 Starting AnyLab Frontend..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found!"
    echo "💡 Make sure you're in the frontend directory:"
    echo "   cd /Volumes/Orico/Anylab103/frontend"
    echo "   ./start-frontend.sh"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
echo "🎯 Starting React development server..."
echo "📍 Frontend will be available at: http://localhost:3000"
echo "🔧 Backend should be running at: http://localhost:8001 (changed from 8000 to avoid conflict with 7English)"
echo ""
echo "💡 To stop: Press Ctrl+C"
echo ""

npm start
