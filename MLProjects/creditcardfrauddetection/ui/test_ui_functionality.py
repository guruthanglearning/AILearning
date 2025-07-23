#!/usr/bin/env python
"""
Test script to verify UI functionality for fraud patterns.
"""

import requests
import json

API_URL = "http://localhost:8000"
STREAMLIT_URL = "http://localhost:8501"
API_KEY = "development_api_key_for_testing"

def test_api_connectivity():
    """Test API connectivity and fraud patterns endpoint."""
    print("🧪 Testing API Connectivity and Fraud Patterns")
    print("=" * 50)
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # Test health endpoint
    try:
        response = requests.get(f"{API_URL}/api/v1/health", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check: PASSED")
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   Version: {health_data.get('version')}")
        else:
            print(f"❌ API Health Check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health Check: ERROR - {str(e)}")
        return False
    
    # Test fraud patterns endpoint
    try:
        response = requests.get(f"{API_URL}/api/v1/fraud-patterns", headers=headers, timeout=10)
        if response.status_code == 200:
            patterns = response.json()
            print(f"✅ Fraud Patterns API: PASSED")
            print(f"   Total patterns: {len(patterns)}")
            
            if patterns:
                # Show details of first pattern
                first_pattern = patterns[0]
                print(f"   Sample pattern ID: {first_pattern.get('id', 'Unknown')}")
                print(f"   Sample pattern name: {first_pattern.get('name', 'Unknown')}")
                print(f"   Sample fraud type: {first_pattern.get('pattern', {}).get('fraud_type', 'Unknown')}")
                
                # Count fraud types
                fraud_types = set()
                for pattern in patterns:
                    fraud_type = pattern.get('pattern', {}).get('fraud_type', 'Unknown')
                    if fraud_type:
                        fraud_types.add(fraud_type)
                
                print(f"   Unique fraud types: {len(fraud_types)}")
                print(f"   Fraud types: {', '.join(sorted(fraud_types)[:5])}{'...' if len(fraud_types) > 5 else ''}")
                
            return True
        else:
            print(f"❌ Fraud Patterns API: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Fraud Patterns API: ERROR - {str(e)}")
        return False

def test_streamlit_accessibility():
    """Test if Streamlit UI is accessible."""
    print(f"\n🌐 Testing Streamlit UI Accessibility")
    print("=" * 50)
    
    try:
        response = requests.get(STREAMLIT_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit UI: ACCESSIBLE")
            print(f"   URL: {STREAMLIT_URL}")
            print(f"   Status Code: {response.status_code}")
            return True
        else:
            print(f"❌ Streamlit UI: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Streamlit UI: ERROR - {str(e)}")
        return False

def main():
    """Run all UI functionality tests."""
    print("🚀 Starting UI Functionality Tests")
    print("=" * 60)
    
    api_test = test_api_connectivity()
    ui_test = test_streamlit_accessibility()
    
    print("\n📊 Test Results Summary")
    print("=" * 60)
    print(f"API Connectivity: {'✅ PASSED' if api_test else '❌ FAILED'}")
    print(f"Streamlit UI: {'✅ PASSED' if ui_test else '❌ FAILED'}")
    
    if api_test and ui_test:
        print("\n🎉 All tests PASSED! The fraud patterns UI should be working correctly.")
        print("\n📋 Next Steps:")
        print("1. Open browser to http://localhost:8501")
        print("2. Navigate to 'Fraud Patterns' page")
        print("3. Test search and filtering functionality")
        print("4. Test CRUD operations (Add, Edit, Delete patterns)")
        print("5. Verify data display and formatting")
    else:
        print("\n❌ Some tests FAILED. Please check the error messages above.")
    
    return api_test and ui_test

if __name__ == "__main__":
    main()
