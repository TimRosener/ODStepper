#!/bin/bash
echo "=== Checking Git Status ==="
cd /Users/timrosener/Documents/Arduino/libraries/ODStepper
pwd
echo ""
echo "=== Files with changes ==="
git status --porcelain
echo ""
echo "=== Attempting to add and commit ==="
git add -A
git commit -m "Update to non-commercial license (CC BY-NC 4.0)" --verbose
echo ""
echo "=== Commit result: $? ==="
echo ""
echo "=== Current git log ==="
git log --oneline -3
echo ""
echo "=== Remote info ==="
git remote -v
