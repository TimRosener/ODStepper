#!/bin/bash

# STRICT TEMPLATE ENFORCEMENT PRE-COMMIT HOOK
# This hook BLOCKS any commits that violate template or design system standards
# ZERO TOLERANCE - No violations allowed

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 STRICT PRE-COMMIT VALIDATION${NC}"
echo -e "${BLUE}================================${NC}"

# Track if any violations found
VIOLATIONS=0
PROTECTED_VIOLATIONS=0

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
    echo "No files staged for commit"
    exit 0
fi

echo "Checking staged files for violations..."
echo ""

# Check for protected file modifications
echo -e "${BLUE}1. Protected File Check${NC}"
echo "------------------------"

PROTECTED_PATTERNS=(
    "^shared/design-system.css$"
    "^shared/components.css$"
    "^\.claude/agents/.*\.md$"
    "^clone-template\.sh$"
    "^service-manager\.sh$"
    "^\.validation/"
)

for file in $STAGED_FILES; do
    for pattern in "${PROTECTED_PATTERNS[@]}"; do
        if [[ $file =~ $pattern ]]; then
            echo -e "${RED}❌ BLOCKED: Protected file modification: $file${NC}"
            echo -e "${RED}   Protected files cannot be modified${NC}"
            ((PROTECTED_VIOLATIONS++))
            ((VIOLATIONS++))
        fi
    done
done

if [ $PROTECTED_VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ No protected file violations${NC}"
fi

echo ""

# Check CSS and HTML files for violations
echo -e "${BLUE}2. CSS & HTML Validation${NC}"
echo "-------------------------"

CSS_HTML_FILES=$(echo "$STAGED_FILES" | grep -E '\.(css|html)$' || true)

if [ -n "$CSS_HTML_FILES" ]; then
    for file in $CSS_HTML_FILES; do
        if [ -f "$file" ]; then
            echo "Checking: $file"
            
            # Check for inline styles
            if grep -q 'style\s*=' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: Inline styles found in $file${NC}"
                echo -e "${RED}   Remove all style=\"...\" attributes${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for hex colors
            if grep -qE '#[0-9a-fA-F]{3,6}' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: Hex colors found in $file${NC}"
                echo -e "${RED}   Use CSS variables like var(--primary) instead${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for direct pixel values (excluding CSS variables)
            if grep -qE '[^-]\d+px' "$file" 2>/dev/null && ! grep -q 'var(--' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: Direct pixel values found in $file${NC}"
                echo -e "${RED}   Use spacing variables like var(--space-4) instead${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for !important
            if grep -q '!important' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: !important flags found in $file${NC}"
                echo -e "${RED}   Fix CSS specificity instead of using !important${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for custom CSS variables
            if grep -qE '--[a-zA-Z][a-zA-Z0-9-]*\s*:' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: Custom CSS variables found in $file${NC}"
                echo -e "${RED}   Only use variables from design-system.css${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for RGB/RGBA colors
            if grep -qE 'rgba?\s*\(' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: RGB/RGBA colors found in $file${NC}"
                echo -e "${RED}   Use CSS variables instead of RGB colors${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check for color names
            if grep -qEi '\b(red|blue|green|yellow|orange|purple|black|white|gray|grey)\s*[;}]' "$file" 2>/dev/null; then
                echo -e "${RED}❌ BLOCKED: Color names found in $file${NC}"
                echo -e "${RED}   Use CSS variables instead of color names${NC}"
                ((VIOLATIONS++))
            fi
            
            # Check HTML files for CSS import order
            if [[ $file =~ \.html$ ]]; then
                if grep -q 'components\.css.*design-system\.css' "$file" 2>/dev/null; then
                    echo -e "${RED}❌ BLOCKED: Wrong CSS import order in $file${NC}"
                    echo -e "${RED}   design-system.css must come before components.css${NC}"
                    ((VIOLATIONS++))
                fi
                
                # Check for external CSS frameworks
                if grep -qEi '(bootstrap|tailwind|bulma|foundation)' "$file" 2>/dev/null; then
                    echo -e "${RED}❌ BLOCKED: External CSS framework detected in $file${NC}"
                    echo -e "${RED}   Remove external CSS frameworks${NC}"
                    ((VIOLATIONS++))
                fi
            fi
        fi
    done
else
    echo "No CSS/HTML files to validate"
fi

echo ""

# Run the comprehensive Python validator if available
echo -e "${BLUE}3. Comprehensive Validation${NC}"
echo "---------------------------"

VALIDATOR_PATH=".validation/strict-validator.py"
if [ -f "$VALIDATOR_PATH" ]; then
    echo "Running comprehensive validator..."
    if ! python3 "$VALIDATOR_PATH" .; then
        echo -e "${RED}❌ BLOCKED: Comprehensive validation failed${NC}"
        ((VIOLATIONS++))
    else
        echo -e "${GREEN}✅ Comprehensive validation passed${NC}"
    fi
else
    echo "⚠️  Comprehensive validator not found (optional)"
fi

echo ""

# Check project structure integrity
echo -e "${BLUE}4. Project Structure Check${NC}"
echo "---------------------------"

REQUIRED_DIRS=("backend" "frontend" "shared" "docs")
REQUIRED_FILES=("start.sh" "backend/api.py" "frontend/index.html" "shared/design-system.css")

STRUCTURE_OK=true

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ BLOCKED: Missing required directory: $dir${NC}"
        ((VIOLATIONS++))
        STRUCTURE_OK=false
    fi
done

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ BLOCKED: Missing required file: $file${NC}"
        ((VIOLATIONS++))
        STRUCTURE_OK=false
    fi
done

if $STRUCTURE_OK; then
    echo -e "${GREEN}✅ Project structure is intact${NC}"
fi

echo ""

# Final decision
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}COMMIT DECISION${NC}"
echo -e "${BLUE}================================${NC}"

if [ $VIOLATIONS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo -e "${GREEN}Commit approved - No violations detected${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ COMMIT BLOCKED${NC}"
    echo -e "${RED}Total violations found: $VIOLATIONS${NC}"
    echo ""
    echo -e "${YELLOW}To fix violations:${NC}"
    echo "1. Fix all violations listed above"
    echo "2. Stage your fixed files: git add <files>"
    echo "3. Try committing again"
    echo ""
    echo -e "${YELLOW}For help:${NC}"
    echo "• Check design system: shared/design-system.css"
    echo "• Review standards: docs/STANDARDS.md"
    echo "• Run validator: python3 .validation/strict-validator.py"
    echo ""
    
    # Show specific help based on violation types
    if [ $PROTECTED_VIOLATIONS -gt 0 ]; then
        echo -e "${YELLOW}Protected File Help:${NC}"
        echo "• Protected files cannot be modified"
        echo "• To update design system, contact tech lead"
        echo "• Revert protected file changes: git checkout HEAD -- <file>"
        echo ""
    fi
    
    echo -e "${RED}COMMIT REJECTED${NC}"
    exit 1
fi