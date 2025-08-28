#!/bin/bash

# Local test script to verify CI setup
# This script simulates the GitHub Actions environment locally (without PostgreSQL)

set -e

echo "🔧 Setting up environment..."
export CI=true
export GITHUB_ACTIONS=true
export DJANGO_SETTINGS_MODULE=demowebapp.test_settings
export DEBUG=False

echo "📋 Checking Django configuration..."
python3 manage.py check --settings=demowebapp.test_settings

echo "🔍 Showing migration status..."
python3 manage.py showmigrations --settings=demowebapp.test_settings

echo "🗃️ Running migrations..."
python3 manage.py migrate --settings=demowebapp.test_settings

echo "🧪 Running a single test to verify setup..."
python3 manage.py test tests.test_chat_api.ChatAPITestCase.test_chat_create_success --verbosity=2 --settings=demowebapp.test_settings

echo "✅ Local setup verification complete!"
echo "Note: This test used SQLite. In CI, PostgreSQL will be used automatically."
