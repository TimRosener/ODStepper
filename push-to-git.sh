#!/bin/bash

# ODStepper Git Push Script
# This script commits and pushes changes for the ODStepper library

echo "========================================="
echo "ODStepper Library Git Push"
echo "========================================="

# Check if we're in the right directory
if [ ! -f "ODStepper.h" ]; then
    echo "Error: ODStepper.h not found. Are you in the ODStepper directory?"
    exit 1
fi

# Show current status
echo -e "\nCurrent git status:"
git status --short

# Ask for confirmation
echo -e "\nThis will commit ALL changes shown above."
read -p "Do you want to continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Add all changes
echo -e "\nAdding all changes..."
git add .

# Create commit message
COMMIT_MSG="Update to non-commercial license (CC BY-NC 4.0)

- Changed license from MIT to CC BY-NC 4.0
- Added license headers to all source files
- Updated documentation to reflect non-commercial use
- Added commercial licensing contact information
- Updated all metadata files (library.properties, library.json)
- Created professional documentation structure"

# Commit changes
echo -e "\nCommitting changes..."
git commit -m "$COMMIT_MSG"

# Push to main branch
echo -e "\nPushing to origin/main..."
git push origin main

# Ask about creating a release tag
echo -e "\n========================================="
read -p "Do you want to create and push the v1.0.0 release tag? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\nCreating tag v1.0.0..."
    git tag -a v1.0.0 -m "Initial release - Open-drain wrapper for FastAccelStepper (CC BY-NC 4.0)"
    
    echo "Pushing tag to origin..."
    git push origin v1.0.0
    
    echo -e "\n✅ Tag v1.0.0 created and pushed!"
fi

echo -e "\n========================================="
echo "✅ All changes have been pushed to GitHub!"
echo "========================================="

# Reminder about Arduino Library Manager
echo -e "\nNext steps:"
echo "1. Visit https://github.com/TimRosener/ODStepper to verify the push"
echo "2. Create a GitHub release from the v1.0.0 tag"
echo "3. Submit to Arduino Library Manager:"
echo "   https://github.com/arduino/library-registry/issues/new/choose"
echo ""
echo "Note: The library is licensed for non-commercial use only (CC BY-NC 4.0)"
