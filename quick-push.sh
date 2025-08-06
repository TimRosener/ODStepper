#!/bin/bash

# Quick push script for ODStepper
# Usage: ./quick-push.sh "Your commit message"

if [ -z "$1" ]; then
    echo "Usage: ./quick-push.sh \"Your commit message\""
    exit 1
fi

echo "Pushing changes with message: $1"
git add .
git commit -m "$1"
git push origin main

echo "✅ Done!"
