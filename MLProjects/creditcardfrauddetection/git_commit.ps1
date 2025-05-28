#!/bin/pwsh
Set-Location D:\Study\AILearning\MLProjects\creditcardfrauddetection
git add README.md
git add RUN_INSTRUCTIONS.md 
git add app/services/vector_db_service.py 
git add app/api/endpoints.py 
git add ui/api_client.py 
git add ui/pages/fraud_patterns.py 
git add run_ui_fixed.ps1 
git add start_api.ps1 
git add start_system.ps1
git commit -m "Fix Fraud Patterns UI to use real data instead of mock data

- Fixed vector database complex metadata handling
- Fixed API client indentation issues and added PUT support
- Updated documentation and simplified script structure
- Removed redundant files and moved them to backup
- Enhanced README.md with recent improvements section"

git push
