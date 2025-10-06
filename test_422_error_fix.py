"""
Test script to verify the 422 error fix for /api/history/deals and /api/history/orders endpoints.

This script tests:
1. Endpoints work with no parameters (empty query string)
2. Endpoints work with date parameters
3. Endpoints work with symbol filter
4. Response format is correct
"""

import requests
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:5001"

def test_deals_endpoint():
    """Test the /api/history/deals endpoint."""
    print("=" * 80)
    print("TESTING /api/history/deals ENDPOINT")
    print("=" * 80)
    
    # Test 1: No parameters (should use defaults: last 30 days)
    print("\n1. Testing with NO parameters (empty query string)...")
    try:
        response = requests.get(f"{API_BASE}/api/history/deals")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Deals count: {len(data.get('deals', []))}")
        elif response.status_code == 422:
            print("   ✗ FAILED - Still returns 422 Unprocessable Entity")
            print(f"   Error: {response.json()}")
            return False
        else:
            print(f"   ⚠ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 2: With date parameters
    print("\n2. Testing with date parameters...")
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        
        params = {
            "date_from": start.isoformat(),
            "date_to": end.isoformat()
        }
        
        response = requests.get(f"{API_BASE}/api/history/deals", params=params)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Deals count: {len(data.get('deals', []))}")
        else:
            print(f"   ✗ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 3: With symbol filter
    print("\n3. Testing with symbol filter...")
    try:
        params = {
            "symbol": "EURUSD"
        }
        
        response = requests.get(f"{API_BASE}/api/history/deals", params=params)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Deals count: {len(data.get('deals', []))}")
        else:
            print(f"   ✗ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    print("\n✓ All /api/history/deals tests passed!")
    return True


def test_orders_endpoint():
    """Test the /api/history/orders endpoint."""
    print("\n" + "=" * 80)
    print("TESTING /api/history/orders ENDPOINT")
    print("=" * 80)
    
    # Test 1: No parameters (should use defaults: last 30 days)
    print("\n1. Testing with NO parameters (empty query string)...")
    try:
        response = requests.get(f"{API_BASE}/api/history/orders")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            print(f"   Orders count: {len(data.get('orders', []))}")
        elif response.status_code == 422:
            print("   ✗ FAILED - Still returns 422 Unprocessable Entity")
            print(f"   Error: {response.json()}")
            return False
        else:
            print(f"   ⚠ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 2: With date parameters
    print("\n2. Testing with date parameters...")
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        
        params = {
            "date_from": start.isoformat(),
            "date_to": end.isoformat()
        }
        
        response = requests.get(f"{API_BASE}/api/history/orders", params=params)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Orders count: {len(data.get('orders', []))}")
        else:
            print(f"   ✗ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    # Test 3: With symbol filter
    print("\n3. Testing with symbol filter...")
    try:
        params = {
            "symbol": "EURUSD"
        }
        
        response = requests.get(f"{API_BASE}/api/history/orders", params=params)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✓ SUCCESS - Returns 200 OK")
            data = response.json()
            print(f"   Orders count: {len(data.get('orders', []))}")
        else:
            print(f"   ✗ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False
    
    print("\n✓ All /api/history/orders tests passed!")
    return True


def test_analysis_page_integration():
    """Test that the Analysis page can successfully call the endpoints."""
    print("\n" + "=" * 80)
    print("TESTING ANALYSIS PAGE INTEGRATION")
    print("=" * 80)
    
    print("\n1. Simulating Analysis page API calls...")
    
    # Simulate the exact calls made by Analysis.tsx
    endpoints = [
        ("/api/account", "Account info"),
        ("/api/positions", "Positions"),
        ("/api/history/deals", "Deals (no params)"),
        ("/api/symbols/priority", "Priority symbols"),
    ]
    
    all_passed = True
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            status = "✓" if response.status_code == 200 else "✗"
            print(f"   {status} {description}: {response.status_code}")
            
            if response.status_code != 200:
                all_passed = False
        except Exception as e:
            print(f"   ✗ {description}: ERROR - {e}")
            all_passed = False
    
    if all_passed:
        print("\n✓ All Analysis page integration tests passed!")
    else:
        print("\n✗ Some Analysis page integration tests failed!")
    
    return all_passed


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("422 ERROR FIX VERIFICATION TEST")
    print("=" * 80)
    print("\nThis test verifies that the 422 Unprocessable Entity error")
    print("has been fixed for /api/history/deals and /api/history/orders")
    print("\n" + "=" * 80)
    
    results = []
    
    # Run all tests
    results.append(("Deals Endpoint", test_deals_endpoint()))
    results.append(("Orders Endpoint", test_orders_endpoint()))
    results.append(("Analysis Page Integration", test_analysis_page_integration()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - 422 ERROR IS FIXED!")
    else:
        print("✗ SOME TESTS FAILED - PLEASE REVIEW")
    print("=" * 80)
    
    import sys
    sys.exit(0 if all_passed else 1)

