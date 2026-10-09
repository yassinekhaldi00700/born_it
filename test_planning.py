#!/usr/bin/env python3
"""
Simple test script to check if the planning endpoint works
"""

import requests
import json

def test_planning_endpoint():
    try:
        # Test the planning endpoint
        url = "http://localhost:5000/getplanning"  # Adjust port if needed
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nPlanning Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: Make sure the Flask app is running")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_planning_endpoint()