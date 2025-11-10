// Fix html-webpack-plugin to use relative paths
const fs = require('fs');
const path = require('path');

const indexPath = path.join(__dirname, 'node_modules', 'html-webpack-plugin', 'index.js');
const content = fs.readFileSync(indexPath, 'utf8');

// Replace absolute path resolution with relative path
const fixed = content.replace(
  /require\.resolve\(["']\.\/lib\/loader\.js["']\)/g,
  "path.resolve(__dirname, 'lib', 'loader.js')"
);

if (content !== fixed) {
  fs.writeFileSync(indexPath, fixed);
  console.log('✅ Fixed html-webpack-plugin index.js');
} else {
  console.log('⚠️  No changes needed (or pattern not found)');
}
