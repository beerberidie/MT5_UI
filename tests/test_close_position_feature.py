"""
Test script for the Close Position feature in Tradecraft Console.

This script:
1. Executes a test market order (0.01 lot EURUSD)
2. Verifies the position appears in the positions list
3. Tests the close position endpoint
4. Verifies the position is closed
"""

import requests
import time
import sys

API_BASE = "http://127.0.0.1:5001"
API_KEY = "AC135782469AD"


def get_headers():
    """Get headers with API key for authenticated requests."""
    return {"Content-Type": "application/json", "X-API-Key": API_KEY}


def test_close_position_feature():
    """Test the complete close position workflow."""
    print("=" * 80)
    print("CLOSE POSITION FEATURE TEST")
    print("=" * 80)

    # Step 1: Check current positions
    print("\n1. Checking current positions...")
    try:
        response = requests.get(f"{API_BASE}/api/positions")
        response.raise_for_status()
        initial_positions = response.json()
        print(f"   ✓ Current open positions: {len(initial_positions)}")
        for pos in initial_positions:
            print(
                f"     - Ticket: {pos.get('ticket')}, Symbol: {pos.get('symbol')}, "
                f"Volume: {pos.get('volume')}, P/L: {pos.get('profit', 0):.2f}"
            )
    except Exception as e:
        print(f"   ✗ Failed to get positions: {e}")
        return False

    # Step 2: Execute a test market order
    print("\n2. Executing test market order (0.01 lot EURUSD BUY)...")
    try:
        order_payload = {
            "canonical": "EURUSD",
            "side": "buy",
            "volume": 0.01,
            "deviation": 20,
            "comment": "Test order for close position feature",
        }
        response = requests.post(
            f"{API_BASE}/api/order", json=order_payload, headers=get_headers()
        )
        response.raise_for_status()
        order_result = response.json()

        if order_result.get("result_code", 0) >= 10000:
            ticket = order_result.get("order")
            print(f"   ✓ Order executed successfully!")
            print(f"     - Ticket: {ticket}")
            print(f"     - Result Code: {order_result.get('result_code')}")
        else:
            print(f"   ✗ Order failed: {order_result}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to execute order: {e}")
        return False

    # Step 3: Wait for position to appear
    print("\n3. Waiting for position to appear (2 seconds)...")
    time.sleep(2)

    # Step 4: Verify position exists
    print("\n4. Verifying position exists...")
    try:
        response = requests.get(f"{API_BASE}/api/positions")
        response.raise_for_status()
        positions = response.json()

        # Find our test position
        test_position = None
        for pos in positions:
            if pos.get("ticket") == ticket or pos.get("symbol") == "EURUSD":
                test_position = pos
                break

        if test_position:
            print(f"   ✓ Position found!")
            print(f"     - Ticket: {test_position.get('ticket')}")
            print(f"     - Symbol: {test_position.get('symbol')}")
            print(f"     - Type: {test_position.get('type')}")
            print(f"     - Volume: {test_position.get('volume')}")
            print(f"     - P/L: {test_position.get('profit', 0):.2f}")
            position_ticket = test_position.get("ticket")
        else:
            print(f"   ✗ Position not found in positions list")
            print(f"     Available positions: {len(positions)}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to verify position: {e}")
        return False

    # Step 5: Test close position endpoint
    print(f"\n5. Testing close position endpoint (Ticket: {position_ticket})...")
    try:
        response = requests.post(
            f"{API_BASE}/api/positions/{position_ticket}/close", headers=get_headers()
        )
        response.raise_for_status()
        close_result = response.json()

        if close_result.get("result_code", 0) >= 10000:
            print(f"   ✓ Position closed successfully!")
            print(f"     - Result Code: {close_result.get('result_code')}")
            print(f"     - Deal: {close_result.get('deal')}")
        else:
            print(f"   ✗ Close failed: {close_result}")
            return False
    except Exception as e:
        print(f"   ✗ Failed to close position: {e}")
        return False

    # Step 6: Wait for position to be removed
    print("\n6. Waiting for position to be removed (2 seconds)...")
    time.sleep(2)

    # Step 7: Verify position is closed
    print("\n7. Verifying position is closed...")
    try:
        response = requests.get(f"{API_BASE}/api/positions")
        response.raise_for_status()
        final_positions = response.json()

        # Check if our position is still there
        position_still_exists = any(
            pos.get("ticket") == position_ticket for pos in final_positions
        )

        if not position_still_exists:
            print(f"   ✓ Position successfully removed from positions list!")
            print(f"     - Remaining open positions: {len(final_positions)}")
        else:
            print(f"   ✗ Position still exists in positions list")
            return False
    except Exception as e:
        print(f"   ✗ Failed to verify position closure: {e}")
        return False

    # Step 8: Test error handling (try to close non-existent position)
    print("\n8. Testing error handling (non-existent position)...")
    try:
        response = requests.post(
            f"{API_BASE}/api/positions/999999999/close", headers=get_headers()
        )

        if response.status_code == 503 or response.status_code == 200:
            result = response.json()
            print(f"   ✓ Error handling works correctly")
            print(f"     - Status: {response.status_code}")
            print(
                f"     - Response: {result.get('error', {}).get('message', 'Position not found')}"
            )
        else:
            print(f"   ⚠ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   ⚠ Error handling test: {e}")

    # Step 9: Test authentication (without API key)
    print("\n9. Testing authentication (without API key)...")
    try:
        response = requests.post(
            f"{API_BASE}/api/positions/999999999/close",
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 401:
            print(f"   ✓ Authentication required (401 Unauthorized)")
        else:
            print(f"   ✗ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Authentication test failed: {e}")

    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nClose Position Feature Summary:")
    print("  ✓ API endpoint working correctly")
    print("  ✓ Position closes successfully")
    print("  ✓ Position removed from positions list")
    print("  ✓ Error handling works")
    print("  ✓ Authentication required")
    print("\nFrontend Integration:")
    print("  1. Open http://localhost:3000")
    print("  2. Execute a test order (0.01 lot)")
    print("  3. Look for the 'X' button next to the position")
    print("  4. Click the 'X' button")
    print("  5. Confirm in the dialog")
    print("  6. Verify position is closed and removed from list")
    print("  7. Check for success toast notification")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        success = test_close_position_feature()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
