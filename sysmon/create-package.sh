#!/bin/bash

# OnLab SysMon Agent - Package Creation Script
# This script creates a deployment package for the SysMon agent

set -e

PACKAGE_NAME="onlab-sysmon-agent"
VERSION="2.0.0"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📦 Creating OnLab SysMon Agent Package v$VERSION"

# Create package directory
PACKAGE_DIR="${PACKAGE_NAME}-${VERSION}"
mkdir -p $PACKAGE_DIR

# Copy required files
echo "📋 Copying files..."
cp -r sysmon_project/ $PACKAGE_DIR/
cp deploy-client.sh $PACKAGE_DIR/
cp DEPLOYMENT_GUIDE.md $PACKAGE_DIR/

# Create README for the package
cat > $PACKAGE_DIR/README.md << EOF
# OnLab SysMon Agent v$VERSION

## Quick Start

1. **Extract the package:**
   \`\`\`bash
   tar -xzf $PACKAGE_NAME-$VERSION.tar.gz
   cd $PACKAGE_NAME-$VERSION
   \`\`\`

2. **Edit configuration:**
   \`\`\`bash
   # Edit deploy-client.sh and update:
   # - ONELAB_SERVER (your OnLab server IP)
   # - API_KEY (get from OnLab admin panel)
   nano deploy-client.sh
   \`\`\`

3. **Deploy:**
   \`\`\`bash
   sudo ./deploy-client.sh
   \`\`\`

## Requirements
- Python 3.7+
- Root/sudo access
- Network connectivity to OnLab server

## Support
See DEPLOYMENT_GUIDE.md for detailed instructions.
EOF

# Create the tar.gz package
echo "🗜️  Creating package..."
tar -czf "${PACKAGE_NAME}-${VERSION}.tar.gz" $PACKAGE_DIR/

# Clean up
rm -rf $PACKAGE_DIR

echo "✅ Package created: ${PACKAGE_NAME}-${VERSION}.tar.gz"
echo ""
echo "📤 To deploy to a client:"
echo "   scp ${PACKAGE_NAME}-${VERSION}.tar.gz user@client-ip:/tmp/"
echo "   ssh user@client-ip"
echo "   cd /tmp && tar -xzf ${PACKAGE_NAME}-${VERSION}.tar.gz"
echo "   cd ${PACKAGE_NAME}-${VERSION}"
echo "   sudo ./deploy-client.sh"
