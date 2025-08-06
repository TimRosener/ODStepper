#!/bin/bash

# ODStepper Git Push Script - Debug Version
# This script commits and pushes changes for the ODStepper library

echo "========================================="
echo "ODStepper Library Git Push (Debug Version)"
echo "========================================="

# Show current directory
echo "Current directory: $(pwd)"

# Check if we're in the right directory
if [ ! -f "ODStepper.h" ]; then
    echo "Error: ODStepper.h not found. Are you in the ODStepper directory?"
    echo "Files in current directory:"
    ls -la
    exit 1
fi

# Check git repository
echo ""
echo "Git remote configuration:"
git remote -v

# Show current status
echo ""
echo "Current git status:"
git status

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo ""
    echo "No changes to commit. Working directory is clean."
    exit 0
fi

# Ask for confirmation
echo ""
echo "This will commit ALL changes shown above."
read -p "Do you want to continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Add all changes
echo ""
echo "Adding all changes..."
git add -A
echo "Files staged:"
git status --short

# Create commit message
COMMIT_MSG="Update to non-commercial license (CC BY-NC 4.0)

- Changed license from MIT to CC BY-NC 4.0
- Added license headers to all source files
- Updated documentation to reflect non-commercial use
- Added commercial licensing contact information
- Updated all metadata files (library.properties, library.json)
- Created professional documentation structure"

# Commit changes
echo ""
echo "Committing changes..."
git commit -m "$COMMIT_MSG"
COMMIT_RESULT=$?

if [ $COMMIT_RESULT -ne 0 ]; then
    echo "Error: Commit failed with exit code $COMMIT_RESULT"
    exit 1
fi

# Push to main branch
echo ""
echo "Pushing to origin/main..."
git push origin main
PUSH_RESULT=$?

if [ $PUSH_RESULT -ne 0 ]; then
    echo "Error: Push failed with exit code $PUSH_RESULT"
    echo "This might be due to:"
    echo "1. Authentication issues (check your GitHub credentials)"
    echo "2. Network connection problems"
    echo "3. Remote repository permissions"
    exit 1
fi

# Ask about creating a release tag
echo ""
echo "========================================="
read -p "Do you want to create and push the v1.0.0 release tag? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if tag already exists
    if git rev-parse v1.0.0 >/dev/null 2>&1; then
        echo "Warning: Tag v1.0.0 already exists!"
        read -p "Do you want to delete and recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git tag -d v1.0.0
            git push origin :refs/tags/v1.0.0
        else
            echo "Skipping tag creation."
        fi
    fi
    
    echo ""
    echo "Creating tag v1.0.0..."
    git tag -a v1.0.0 -m "Initial release - Open-drain wrapper for FastAccelStepper (CC BY-NC 4.0)"
    
    echo "Pushing tag to origin..."
    git push origin v1.0.0
    TAG_RESULT=$?
    
    if [ $TAG_RESULT -eq 0 ]; then
        echo ""
        echo "✅ Tag v1.0.0 created and pushed!"
    else
        echo "Error: Tag push failed with exit code $TAG_RESULT"
    fi
fi

echo ""
echo "========================================="
echo "✅ Process completed!"
echo "========================================="

# Show final status
echo ""
echo "Final git status:"
git status --short
echo ""
echo "Recent commits:"
git log --oneline -5

echo ""
echo "Next steps:"
echo "1. Visit https://github.com/TimRosener/ODStepper to verify the push"
echo "2. Create a GitHub release from the v1.0.0 tag (if created)"
echo "3. Submit to Arduino Library Manager:"
echo "   https://github.com/arduino/library-registry/issues/new/choose"
echo ""
echo "Note: The library is licensed for non-commercial use only (CC BY-NC 4.0)"
