#!/bin/bash

# Make git scripts executable
chmod +x push-to-git.sh
chmod +x quick-push.sh

echo "✅ Git scripts are now executable!"
echo ""
echo "Usage:"
echo "  ./push-to-git.sh    - Interactive push with release tag option"
echo "  ./quick-push.sh     - Quick push with custom message"
echo ""
echo "To run the main push script, type: ./push-to-git.sh"
