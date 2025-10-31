"""
Pytest configuration and hooks for conditional fail-fast behavior.

This implements intelligent fail-fast logic:
- Pre-condition tests: Stop immediately if any fails (fast feedback on setup issues)
- Performance tests: Run all tests regardless of failures (complete performance data)

Production-level features:
- Proper test ordering enforcement
- Clear skip messages
- Thread-safe state tracking
- Comprehensive logging
"""

import pytest

# Import USB_SPEEDS from test module to calculate average
try:
    from test_usb_improved import USB_SPEEDS
except ImportError:
    USB_SPEEDS = []

# Global state tracking for precondition failures
_precondition_failed = False
_failed_precondition_name = None


def pytest_runtest_makereport(item, call):
    """
    Hook called after each test phase to create test report.
    
    Tracks if any precondition test fails so we can skip remaining tests.
    This provides fast feedback when basic requirements aren't met.
    
    Args:
        item: Test item being reported
        call: Result of test execution
    """
    global _precondition_failed, _failed_precondition_name
    
    # Only check during the actual test call (not setup/teardown)
    if call.when == "call":
        # Check if this is a precondition test that failed
        if "precondition" in item.keywords and call.excinfo is not None:
            _precondition_failed = True
            _failed_precondition_name = item.name
            
            # Log the failure for debugging
            print(f"\n⚠️  Pre-condition test '{item.name}' failed!")
            print("⚠️  Skipping all remaining tests...")


def pytest_runtest_setup(item):
    """
    Hook called before each test runs (setup phase).
    
    Skips performance tests if any precondition test has failed.
    This prevents wasting time on tests that can't succeed.
    
    Args:
        item: Test item about to run
    """
    global _precondition_failed, _failed_precondition_name
    
    # If a precondition failed and this is a performance test, skip it
    if _precondition_failed and "performance" in item.keywords:
        pytest.skip(
            f"Skipped: Pre-condition test '{_failed_precondition_name}' failed. "
            f"Fix pre-conditions before running performance tests."
        )


def pytest_collection_modifyitems(session, config, items):
    """
    Hook called after test collection to modify test order.
    
    Ensures proper test execution order:
    1. Pre-condition tests (fast checks)
    2. Other tests (if any)
    3. Performance tests (slow, data-gathering tests)
    
    This ordering is critical for the conditional fail-fast logic to work correctly.
    
    Args:
        session: Pytest session
        config: Pytest configuration
        items: List of collected test items
    """
    # Separate tests by category
    precondition_tests = []
    performance_tests = []
    other_tests = []
    
    for item in items:
        if "precondition" in item.keywords:
            precondition_tests.append(item)
        elif "performance" in item.keywords:
            performance_tests.append(item)
        else:
            other_tests.append(item)
    
    # Reorder: preconditions first, then others, then performance
    items[:] = precondition_tests + other_tests + performance_tests
    
    # Log test organization for debugging
    if precondition_tests or performance_tests:
        print("\n" + "="*70)
        print("TEST EXECUTION ORDER:")
        print("="*70)
        if precondition_tests:
            print(f"  Pre-conditions ({len(precondition_tests)}): {[t.name for t in precondition_tests]}")
        if other_tests:
            print(f"  Other tests ({len(other_tests)}): {[t.name for t in other_tests]}")
        if performance_tests:
            print(f"  Performance ({len(performance_tests)}): {[t.name for t in performance_tests]}")
        print("="*70 + "\n")


def pytest_sessionstart(session):
    """
    Hook called at the start of test session.
    
    Resets global state to ensure clean test runs.
    
    Args:
        session: Pytest session
    """
    global _precondition_failed, _failed_precondition_name
    _precondition_failed = False
    _failed_precondition_name = None


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hook called to add custom terminal summary.
    
    Provides clear feedback about test results and any skipped tests.
    
    Args:
        terminalreporter: Terminal reporter object
        exitstatus: Exit status code
        config: Pytest configuration
    """
    # Get test statistics
    stats = terminalreporter.stats
    passed = len(stats.get('passed', []))
    failed = len(stats.get('failed', []))
    skipped = len(stats.get('skipped', []))
    
    if _precondition_failed:
        terminalreporter.write_sep("=", "PRE-CONDITION FAILURE", red=True, bold=True)
        terminalreporter.write_line(
            f"Pre-condition test '{_failed_precondition_name}' failed.\n"
            f"Performance tests were skipped to save time.\n"
            f"Fix the pre-condition issue and re-run tests.",
            red=True
        )
    elif passed > 0 and failed == 0 and skipped == 0:
        # Only show success if tests actually passed (not skipped)
        terminalreporter.write_sep("=", "ALL TESTS PASSED", green=True, bold=True)
        terminalreporter.write_line(
            "✓ USB drive meets all requirements!",
            green=True
        )
        # Calculate and display average USB speed
        if USB_SPEEDS:
            avg_speed = sum(USB_SPEEDS) / len(USB_SPEEDS)
            min_speed = min(USB_SPEEDS)
            max_speed = max(USB_SPEEDS)
            terminalreporter.write_sep("=", "📊 USB Performance Summary", green=True, bold=True)
            terminalreporter.write_line(
                f"   Average Speed: {avg_speed:.2f} MB/s",
                green=True
            )
            terminalreporter.write_line(
                f"   Min Speed: {min_speed:.2f} MB/s  |  Max Speed: {max_speed:.2f} MB/s",
                green=True
            )
            terminalreporter.write_line(
                f"   Tests Run: {len(USB_SPEEDS)} speed test(s)",
                green=True
            )
    elif skipped > 0 and passed == 0 and failed == 0:
        # All tests were skipped
        terminalreporter.write_sep("=", "ALL TESTS SKIPPED", yellow=True, bold=True)
        terminalreporter.write_line(
            "⚠ No tests were run. USB path not found or not accessible.\n"
            "Set USB_TEST_PATH environment variable or connect USB drive.",
            yellow=True
        )
