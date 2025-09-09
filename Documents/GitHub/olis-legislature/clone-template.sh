#!/bin/bash

# AI Agent Starter Template Cloning Script
# Creates a new project from the template with customized names and clean structure

set -e  # Exit on any error

# Color codes for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Template directory (where this script is located)
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}🚀 AI Agent Starter Template Cloner${NC}"
echo ""

# Get project details from user
if [ $# -eq 0 ]; then
    # Interactive mode
    read -p "Enter project folder name (e.g., 'my-app'): " PROJECT_FOLDER
    read -p "Enter application display name (e.g., 'My Application'): " APP_DISPLAY_NAME
    read -p "Enter brief description: " APP_DESCRIPTION
else
    # Command line arguments
    PROJECT_FOLDER=$1
    APP_DISPLAY_NAME=${2:-$PROJECT_FOLDER}
    APP_DESCRIPTION=${3:-"An AI Agent application built from the starter template"}
fi

# Validate input
if [ -z "$PROJECT_FOLDER" ]; then
    echo -e "${RED}❌ Project folder name is required${NC}"
    exit 1
fi

if [ -z "$APP_DISPLAY_NAME" ]; then
    APP_DISPLAY_NAME=$PROJECT_FOLDER
fi

# Create target directory
TARGET_DIR="../$PROJECT_FOLDER"

if [ -d "$TARGET_DIR" ]; then
    echo -e "${RED}❌ Directory $TARGET_DIR already exists${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}📋 Project Details:${NC}"
echo "   Folder: $PROJECT_FOLDER"
echo "   Name: $APP_DISPLAY_NAME"
echo "   Description: $APP_DESCRIPTION"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo -e "${GREEN}📁 Creating new project...${NC}"

# Copy template to new directory (excluding git, venv, data, and this script)
rsync -av \
    --exclude='.git/' \
    --exclude='venv/' \
    --exclude='data/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='clone-template.sh' \
    --exclude='.DS_Store' \
    "$TEMPLATE_DIR/" "$TARGET_DIR/"

echo "   Template copied ✓"

# Make scripts executable
chmod +x "$TARGET_DIR/service-manager.sh"
if [ -f "$TARGET_DIR/setup.sh" ]; then
    chmod +x "$TARGET_DIR/setup.sh"
fi
ln -sf service-manager.sh "$TARGET_DIR/start.sh"  # Compatibility link

# Convert app display name to various formats
APP_SLUG=$(echo "$APP_DISPLAY_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
APP_CLASS=$(echo "$APP_DISPLAY_NAME" | sed 's/[^a-zA-Z0-9]//g')
APP_API_TITLE="$APP_DISPLAY_NAME API"

echo -e "${GREEN}🔄 Customizing project files...${NC}"

# Function to replace text in files
replace_in_file() {
    local file="$1"
    local old="$2"
    local new="$3"
    
    if [ -f "$file" ]; then
        sed -i '' "s|$old|$new|g" "$file" 2>/dev/null || sed -i "s|$old|$new|g" "$file"
    fi
}

# Replace template placeholders in all relevant files
FILES_TO_UPDATE=(
    "$TARGET_DIR/start.sh"
    "$TARGET_DIR/frontend/index.html"
    "$TARGET_DIR/backend/api.py"
    "$TARGET_DIR/.env.example"
)

for file in "${FILES_TO_UPDATE[@]}"; do
    # App name replacements
    replace_in_file "$file" "Task Management Example" "$APP_DISPLAY_NAME"
    replace_in_file "$file" "Task Management" "$APP_DISPLAY_NAME"
    replace_in_file "$file" "Task Management API" "$APP_API_TITLE"
    replace_in_file "$file" "Task Management Dashboard" "$APP_DISPLAY_NAME Dashboard"
    
    # Description replacements
    replace_in_file "$file" "Simple task management service demonstrating the starter template" "$APP_DESCRIPTION"
done

# Update package.json style files if they exist
replace_in_file "$TARGET_DIR/.env.example" "My Application" "$APP_DISPLAY_NAME"

echo "   App name updated in all files ✓"

# Create a clean README for the new project
cat > "$TARGET_DIR/README.md" << EOF
# $APP_DISPLAY_NAME

$APP_DESCRIPTION

## Quick Start

1. **Start the application**:
   \`\`\`bash
   ./start.sh
   \`\`\`

2. **Open your browser** to http://localhost:8000

The application will:
- Create a Python virtual environment (first run)
- Install dependencies automatically  
- Start the backend API server
- Open your dashboard in the browser
- Handle graceful shutdown with Ctrl+C

## Development

This project was created from the AI Agent Starter Template. It includes:

- 🎨 **Unified design system** - Consistent styling using the shared CSS framework
- 📦 **FastAPI backend** - RESTful API with SQLite storage
- 🌐 **Interactive frontend** - Dashboard with real-time updates
- 🔧 **Development tools** - Hot reload, error handling, logging
- 📱 **Responsive design** - Works on desktop, tablet, and mobile

### Project Structure

\`\`\`
$PROJECT_FOLDER/
├── backend/
│   ├── api.py              # FastAPI application with your endpoints
│   ├── storage.py          # SQLite database operations  
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main dashboard page
│   ├── app.js              # Dashboard JavaScript
│   └── style.css           # Page-specific styles
├── shared/                 # Design system (don't modify)
│   ├── design-system.css   # Core variables and styles
│   ├── components.css      # Reusable UI components
│   └── examples.html       # Component reference
└── start.sh                # One-command startup
\`\`\`

### API Endpoints

- \`GET /health\` - Health check
- \`GET /api/status\` - Application status with metrics  
- \`GET /api/activity\` - Recent activity events

Add your own endpoints following the same patterns in \`backend/api.py\`.

### Design System

Use the shared design system components:
- Import stylesheets: \`design-system.css\` → \`components.css\` → \`style.css\`
- View components: http://localhost:8000/examples
- Use CSS variables: \`--primary\`, \`--success\`, \`--space-4\`, etc.

### Storage

Use the \`Storage\` class for data persistence:

\`\`\`python
from storage import Storage

storage = Storage()
storage.set_state("config", {"setting": "value"})
storage.log_event("user_action", {"details": "..."})
\`\`\`

### Environment Variables

Copy \`.env.example\` to \`.env\` and customize:

\`\`\`bash
cp .env.example .env
\`\`\`

## Troubleshooting

### Port 8000 in Use
\`\`\`bash
lsof -i :8000          # Find what's using the port
kill -9 <PID>          # Kill the process  
\`\`\`

### Reset Everything
\`\`\`bash
rm -rf venv data       # Remove virtual env and database
./start.sh             # Start fresh
\`\`\`

---

Built with the **AI Agent Starter Template** 🤖
EOF

echo "   Clean README created ✓"

# Remove example-specific content and comments
echo -e "${GREEN}🧹 Cleaning up example content...${NC}"

# Remove the example banner from index.html
if [ -f "$TARGET_DIR/frontend/index.html" ]; then
    # Remove the example notice banner
    sed -i '' '/<!-- Example Notice Banner -->/,/<!-- Status Header -->/c\
        <!-- Status Header -->' "$TARGET_DIR/frontend/index.html" 2>/dev/null || \
    sed -i '/<!-- Example Notice Banner -->/,/<!-- Status Header -->/c\
        <!-- Status Header -->' "$TARGET_DIR/frontend/index.html"
fi

echo "   Example banner removed ✓"

# Initialize git repository
echo -e "${GREEN}📚 Initializing git repository...${NC}"
cd "$TARGET_DIR"
git init
git add .
git commit -m "Initial commit from AI Agent Starter Template

Generated with clone-template.sh
- App: $APP_DISPLAY_NAME  
- Description: $APP_DESCRIPTION

🤖 Based on AI Agent Starter Template"

echo "   Git repository initialized ✓"

echo ""
echo -e "${GREEN}✨ Project created successfully!${NC}"
echo ""
echo -e "${BLUE}📁 Location:${NC} $TARGET_DIR"
echo -e "${BLUE}🚀 To start:${NC} cd $PROJECT_FOLDER && ./start.sh"
echo -e "${BLUE}🌐 URL:${NC} http://localhost:8000"
echo -e "${BLUE}📖 Components:${NC} http://localhost:8000/examples"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. cd $PROJECT_FOLDER"
echo "2. ./start.sh"
echo "3. Customize backend/api.py with your logic"
echo "4. Update frontend/index.html with your UI"
echo "5. Keep the design system - don't modify shared/ files"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"