#!/bin/bash

# Hook Installation Script
# Installs strict enforcement pre-commit hooks in any project

echo "🔒 Installing Strict Enforcement Hooks"
echo "======================================"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Run this script from the root of your project"
    exit 1
fi

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the pre-commit hook
HOOK_SOURCE=".validation/pre-commit-hook.sh"
HOOK_DEST=".git/hooks/pre-commit"

if [ -f "$HOOK_SOURCE" ]; then
    cp "$HOOK_SOURCE" "$HOOK_DEST"
    chmod +x "$HOOK_DEST"
    echo "✅ Pre-commit hook installed"
else
    echo "❌ Error: pre-commit-hook.sh not found"
    echo "Make sure you're in a project created from the template"
    exit 1
fi

# Test the hook
echo ""
echo "🧪 Testing hook installation..."
if "$HOOK_DEST" --test 2>/dev/null; then
    echo "✅ Hook test passed"
else
    echo "⚠️  Hook test warning (this is normal if no files are staged)"
fi

echo ""
echo "✅ Enforcement hooks installed successfully!"
echo ""
echo "What this means:"
echo "• Every commit will be validated for template compliance"
echo "• Violations will block commits automatically"
echo "• Protected files cannot be modified"
echo "• CSS violations are prevented"
echo ""
echo "To test the hook: stage some files and try to commit"