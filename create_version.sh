#!/bin/bash

# Script to create a new semantic version
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current version
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
echo -e "${BLUE}📋 Current version: ${CURRENT_VERSION}${NC}"

# Parse current version numbers
if [[ $CURRENT_VERSION =~ v([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    MAJOR=${BASH_REMATCH[1]}
    MINOR=${BASH_REMATCH[2]}
    PATCH=${BASH_REMATCH[3]}
else
    echo "❌ Could not parse current version: $CURRENT_VERSION"
    exit 1
fi

# Function to create version
create_version() {
    local new_version=$1
    local description=$2
    
    echo -e "${BLUE}🏷️  Creating new version: ${new_version}${NC}"
    echo -e "${YELLOW}📝 Description: ${description}${NC}"
    
    # Create git tag
    git tag -a "$new_version" -m "$description"
    
    # Update version file
    python update_version.py --from-git
    
    echo -e "${GREEN}✅ Version ${new_version} created successfully!${NC}"
    echo -e "${YELLOW}💡 Don't forget to push the tag: git push origin ${new_version}${NC}"
}

# Show options
echo ""
echo "🚀 Choose version type:"
echo "1) Patch (bug fixes): v${MAJOR}.${MINOR}.$((PATCH+1))"
echo "2) Minor (new features): v${MAJOR}.$((MINOR+1)).0"
echo "3) Major (breaking changes): v$((MAJOR+1)).0.0"
echo "4) Custom version"
echo ""

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        NEW_VERSION="v${MAJOR}.${MINOR}.$((PATCH+1))"
        create_version "$NEW_VERSION" "Patch release: bug fixes and improvements"
        ;;
    2)
        NEW_VERSION="v${MAJOR}.$((MINOR+1)).0"
        create_version "$NEW_VERSION" "Minor release: new features and improvements"
        ;;
    3)
        NEW_VERSION="v$((MAJOR+1)).0.0"
        create_version "$NEW_VERSION" "Major release: breaking changes and new architecture"
        ;;
    4)
        read -p "Enter custom version (e.g., v1.4.0): " CUSTOM_VERSION
        read -p "Enter description: " CUSTOM_DESC
        create_version "$CUSTOM_VERSION" "$CUSTOM_DESC"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
