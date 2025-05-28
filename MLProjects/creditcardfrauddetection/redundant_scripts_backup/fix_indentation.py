"""
Test script to fix indentation issues in fraud_detection_service.py and then import it.
"""

import os
import sys

# Correct the indentation in fraud_detection_service.py
file_path = 'd:/Study/AILearning/MLProjects/creditcardfrauddetection/app/services/fraud_detection_service.py'
with open(file_path, 'r') as f:
    content = f.read()

# Fix indentation issues
content = content.replace("      def get_system_status", "    def get_system_status")
content = content.replace("      def ingest_fraud_patterns", "    def ingest_fraud_patterns")

# Write the corrected content back
with open(file_path, 'w') as f:
    f.write(content)

print("Fixed indentation issues in fraud_detection_service.py")

# Try to import the module
sys.path.append('d:/Study/AILearning/MLProjects/creditcardfrauddetection')
try:
    from app.services.fraud_detection_service import FraudDetectionService
    print("Successfully imported FraudDetectionService")
except Exception as e:
    print(f"Error importing FraudDetectionService: {e}")
