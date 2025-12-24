// Patch script to fix html-webpack-plugin path resolution
const fs = require('fs');
const path = require('path');

const loaderPath = path.join(__dirname, 'node_modules', 'html-webpack-plugin', 'lib', 'loader.js');
const indexPath = path.join(__dirname, 'node_modules', 'html-webpack-plugin', 'index.js');

// Check if files exist
if (fs.existsSync(loaderPath)) {
  console.log('✅ loader.js exists at:', loaderPath);
} else {
  console.log('❌ loader.js NOT found at:', loaderPath);
}

if (fs.existsSync(indexPath)) {
  console.log('✅ index.js exists at:', indexPath);
  const content = fs.readFileSync(indexPath, 'utf8');
  if (content.includes('loader.js')) {
    console.log('⚠️  index.js contains reference to loader.js');
    console.log('Content preview:', content.substring(0, 500));
  }
} else {
  console.log('❌ index.js NOT found');
}
