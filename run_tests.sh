#!/bin/bash
# run_tests.sh - Local Testing Pipeline

echo "🔍 Starting Local Testing Pipeline..."

# 1. Linting Check
echo "Checking code style with flake8..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
if [ $? -ne 0 ]; then
    echo "❌ Linting failed! Please fix errors before committing."
    exit 1
fi
echo "✅ Linting passed."

# 2. Import Verification
echo "Verifying core imports..."
python3 -c "import app; import game_engine; print('✅ Core modules loadable')"
if [ $? -ne 0 ]; then
    echo "❌ Import verification failed!"
    exit 1
fi

# 3. Security Check (Basic)
echo "Checking for exposed secrets..."
grep -r "sk-" . --exclude-dir=venv --exclude-dir=.git
if [ $? -eq 0 ]; then
    echo "⚠️  WARNING: Possible API key found in code!"
else
    echo "✅ No obvious secrets found."
fi

echo "🎉 All local tests passed! Ready to commit."
exit 0
