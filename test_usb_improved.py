"""
USB Speed Test - Production-Ready Implementation

This module tests USB write speed to verify devices meet USB 3.0 minimum requirements.
Tests write data files of various sizes and verify speed is at least 50 MB/s.

Features:
- Cross-platform support (Windows, Linux, macOS)
- Intelligent fail-fast behavior (pre-conditions vs performance tests)
- Parametrized tests for comprehensive performance analysis
- Proper resource cleanup and error handling
- No magic numbers - all constants defined
"""

import logging
import os
import shutil
import time

import pytest

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initial Constants
BYTES_PER_KB = 1024
BYTES_PER_MB = BYTES_PER_KB * 1024

# Constans fot Test configuration
TEST_SIZE_MB = 100  # Default test file size
CHUNK_SIZE_BYTES = 1 * BYTES_PER_MB  # 1MB chunks for more realistic I/O testing
MIN_SPEED_MBPS = 50.0  # Minimum required speed (USB 3.0 spec: 50 ~ 100 MB/s, or more)
SPACE_BUFFER_MULTIPLIER = 1.5  # 50% buffer for space checks (adjust as needed), Use 1 for no buffer.
PROGRESS_LOG_INTERVAL = 10  # Log progress every N chunks. For 1MB chunck, log progress will be for each 10MB, when interval is 10.

# USB Path configuration
DEFAULT_USB_PATH = "/media/tx/USB_DRIVE"
TEST_FILE_NAME = "speedtest.dat"

# Test size configurations for parametrized tests
TEST_SIZES_MB = [50, 100, 200]  # All test file sizes (add more if needed)
MAX_TEST_SIZE_MB = max(TEST_SIZES_MB)  # Largest test file size

# Minimum file size to prevent edge cases
MIN_FILE_SIZE_MB = 1  # Change as needed

# Global list to track USB speeds for final summary
USB_SPEEDS = []


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_usb_path():
    """
    Get USB path from environment variable or use default.

    Environment Variables:
        USB_TEST_PATH: Override default USB mount path

    Returns:
        str: Path to USB drive
    """
    return os.getenv('USB_TEST_PATH', DEFAULT_USB_PATH)


def validate_path(path):
    """
    Validate that path exists and is a directory.

    Args:
        path: Path to validate

    Raises:
        ValueError: If path is invalid
    """
    if not path:
        raise ValueError("Path cannot be empty")

    if not os.path.exists(path):
        raise ValueError(f"Path does not exist: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"Path is not a directory: {path}")


def write_test_file(path, size_mb=TEST_SIZE_MB):
    """
    Write test data to USB and measure write speed.

    This function writes random data in chunks to prevent filesystem
    compression and provides accurate performance measurements.

    Args:
        path: Directory path where test file will be created
        size_mb: Size of test file in megabytes

    Returns:
        float: Write speed in MB/s

    Raises:
        ValueError: If size_mb is invalid or path is invalid
        IOError: If file write operations fail
        OSError: If filesystem operations fail
    """
    # Input file size validation
    if size_mb < MIN_FILE_SIZE_MB:
        raise ValueError(
            f"Invalid size_mb: {size_mb}. Must be at least {MIN_FILE_SIZE_MB} MB."
        )

    validate_path(path)

    test_file = os.path.join(path, TEST_FILE_NAME)
    logger.info(f"Writing {size_mb}MB test file to {test_file}")

    # Calculate number of chunks needed for target size
    total_bytes = size_mb * BYTES_PER_MB
    num_chunks = total_bytes // CHUNK_SIZE_BYTES  # To the nearest integer

    # Handle edge case: file size smaller than chunk size
    if num_chunks == 0:
        # Write a single smaller chunk
        test_chunk = os.urandom(total_bytes)
        num_chunks = 1
    else:
        # Generates random test data
        # Using random data prevents filesystem compression optimizations
        test_chunk = os.urandom(CHUNK_SIZE_BYTES)

    try:
        # Write test file and measure the time
        with open(test_file, 'wb') as f:
            start_time = time.time()

            for i in range(num_chunks):
                bytes_written = f.write(test_chunk)

                # Verify if write succeeded
                if bytes_written != len(test_chunk):
                    raise IOError(
                        f"Write incomplete: expected {len(test_chunk)} bytes, "
                        f"wrote {bytes_written} bytes"
                    )

                # Log progress periodically
                if (i + 1) % PROGRESS_LOG_INTERVAL == 0:
                    progress_mb = (i + 1) * len(test_chunk) / BYTES_PER_MB
                    logger.debug(f"Written {progress_mb:.1f}MB ({(i+1)*100//num_chunks}%)")

            # Ensure data is written to physical device, not just OS cache
            # This is critical for accurate performance measurement
            f.flush()
            os.fsync(f.fileno())

            elapsed = time.time() - start_time

        # Verify file was created successfully
        if not os.path.exists(test_file):
            raise IOError(f"Test file was not created: {test_file}")

        # Calculate actual file size and speed
        actual_size_bytes = os.stat(test_file).st_size
        file_size_mb = actual_size_bytes / BYTES_PER_MB

        # Prevent division by zero
        if elapsed <= 0:
            raise ValueError(f"Invalid elapsed time: {elapsed}s (system clock issue?)")

        speed = file_size_mb / elapsed

        # Reverify that the file size is correct (within 1% tolerance)
        expected_size_mb = size_mb
        size_diff_percent = abs(file_size_mb - expected_size_mb) / expected_size_mb * 100
        if size_diff_percent > 1:
            logger.warning(
                f"File size mismatch: expected {expected_size_mb}MB, "
                f"got {file_size_mb:.2f}MB ({size_diff_percent:.1f}% difference)"
            )

        logger.info(
            f"Write completed: {file_size_mb:.2f}MB in {elapsed:.2f}s = {speed:.2f}MB/s"
        )

        return speed

    except IOError as e:
        logger.error(f"IOError during write to {test_file}: {e}")
        raise IOError(f"Failed to write test file: {e}") from e
    except OSError as e:
        logger.error(f"OSError during write to {test_file}: {e}")
        raise OSError(f"Filesystem error during test: {e}") from e
    finally:
        # Cleanup: Always remove the test file, even if test fails
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
                logger.debug(f"Cleaned up test file: {test_file}")
            except OSError as e:
                # Log if cleanup fails
                logger.warning(f"Could not remove test file {test_file}: {e}")


def get_free_space_mb(path):
    """
    Get available free space on the filesystem (cross-platform).

    Uses shutil.disk_usage() which works on Windows, Linux, and macOS.

    Args:
        path: Path to check (file or directory)

    Returns:
        float: Free space in MB, or None if unavailable
    """
    try:
        # Validate path first
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return None

        disk_usage = shutil.disk_usage(path)
        free_mb = disk_usage.free / BYTES_PER_MB
        total_mb = disk_usage.total / BYTES_PER_MB
        used_mb = disk_usage.used / BYTES_PER_MB

        logger.debug(
            f"Disk usage for {path}: "
            f"Total={total_mb:.0f}MB, Used={used_mb:.0f}MB, Free={free_mb:.0f}MB"
        )

        return free_mb

    except (OSError, AttributeError) as e:
        logger.error(f"Failed to get free space for {path}: {e}")
        return None


# ============================================================================
# PyTest Start: Intial Check USB path before tests
# ============================================================================

@pytest.fixture(scope="function")
def usb_path():
    """
    Fixture that provides validated USB path.

    This fixture ensures the USB path exists before any test runs.
    Tests are skipped if the USB is not connected/mounted.

    Returns:
        str: USB path that exists

    Raises:
        pytest.skip: If USB path is not available
    """
    path = get_usb_path()

    if not os.path.exists(path):
        pytest.skip(f"USB path {path} not found. Is USB drive connected?")

    if not os.path.isdir(path):
        pytest.skip(f"USB path {path} exists but is not a directory")

    logger.info(f"Using USB path: {path}")
    return path


@pytest.fixture(scope="function")
def writable_usb_path(usb_path):
    """
    Fixture that provides validated writable USB path.

    This fixture ensures the USB path is writable before running tests
    that need to write data. Tests are skipped if path is read-only.

    Args:
        usb_path: USB path from usb_path fixture

    Returns:
        str: USB path that exists and is writable

    Raises:
        pytest.skip: If USB path is not writable
    """
    if not os.access(usb_path, os.W_OK):
        pytest.skip(
            f"USB path {usb_path} is not writable. "
            f"Check permissions or if drive is read-only."
        )

    logger.info(f"USB path {usb_path} is writable")
    return usb_path


# ============================================================================
# TESTS - Organized in logical sequence
# ============================================================================
# 1. Pre-condition checks - verify USB is ready
# 2. Edge case tests - validate error handling
# 3. Performance tests - measure USB speed


# ----------------------------------------------------------------------------
# SECTION 1: Pre-condition Checks
# ----------------------------------------------------------------------------
# These tests MUST pass before performance tests run.
# If any pre-condition fails, all remaining tests are skipped (fail-fast).

@pytest.mark.usb
@pytest.mark.precondition
def test_usb_path_writable(usb_path):
    """
    Test 1/6: Verify USB path exists and is writable.

    This is a fast pre-condition check that runs before performance tests.
    CRITICAL: If this fails, all remaining tests are skipped.

    Args:
        usb_path: Fixture providing validated USB path
    """
    assert os.access(usb_path, os.W_OK), (
        f"USB path {usb_path} is not writable. "
        f"Check file permissions or if drive is mounted read-only."
    )
    logger.info(f"✓ USB path {usb_path} is writable")


@pytest.mark.usb
@pytest.mark.precondition
def test_usb_sufficient_space(usb_path):
    """
    Test 2/6: Verify USB has sufficient space for test files.

    This is a fast pre-condition check that prevents test failures
    due to insufficient disk space. Checks for the LARGEST test file size
    to ensure all parametrized tests can run.
    CRITICAL: If this fails, all remaining tests are skipped.

    Args:
        usb_path: Fixture providing validated USB path
    """
    free_mb = get_free_space_mb(usb_path)

    if free_mb is None:
        pytest.skip("Space check not supported on this platform")

    required_mb = MAX_TEST_SIZE_MB * SPACE_BUFFER_MULTIPLIER

    logger.info(
        f"Free space: {free_mb:.0f}MB, Required: {required_mb:.0f}MB "
        f"(for {MAX_TEST_SIZE_MB}MB test + {int((SPACE_BUFFER_MULTIPLIER-1)*100)}% buffer)"
    )

    assert free_mb >= required_mb, (
        f"Insufficient space on USB. "
        f"Required: {required_mb:.0f}MB "
        f"(for {MAX_TEST_SIZE_MB}MB test + {int((SPACE_BUFFER_MULTIPLIER-1)*100)}% buffer), "
        f"Available: {free_mb:.0f}MB. "
        f"Free up {required_mb - free_mb:.0f}MB of space."
    )

    logger.info(f"✓ Sufficient space available for all tests")


# ----------------------------------------------------------------------------
# SECTION 2: Edge Case Tests
# ----------------------------------------------------------------------------

@pytest.mark.usb
@pytest.mark.precondition
def test_invalid_size_raises_error(writable_usb_path):
    """
    Test 3/6: Verify proper error handling for invalid inputs.

    This is a fast edge case test that validates input validation logic.
    CRITICAL: If this fails, all remaining tests are skipped.

    Args:
        writable_usb_path: Fixture providing validated writable USB path
    """
    # Test for negative size
    with pytest.raises(ValueError, match="Invalid size_mb.*Must be at least"):
        write_test_file(writable_usb_path, size_mb=-1)

    # Test forzero size
    with pytest.raises(ValueError, match="Invalid size_mb.*Must be at least"):
        write_test_file(writable_usb_path, size_mb=0)

    # Test for fractional size less than minimum
    with pytest.raises(ValueError, match="Invalid size_mb.*Must be at least"):
        write_test_file(writable_usb_path, size_mb=0.5)

    logger.info("✓ Invalid size error handling works correctly")


# ----------------------------------------------------------------------------
# SECTION 3: Main Functionality Tests (Performance Tests)
# ----------------------------------------------------------------------------
# These tests run ONLY if all pre-conditions pass.
# All performance tests will run regardless of individual failures
# to gather complete performance data across different file sizes.

@pytest.mark.usb
@pytest.mark.performance
@pytest.mark.parametrize("size_mb,expected_min_speed", [
    (size, MIN_SPEED_MBPS) for size in TEST_SIZES_MB
])
def test_usb_speed_parametrized(writable_usb_path, size_mb, expected_min_speed):
    """
    Tests 4-6/6: Test USB speed with different file sizes (parametrized).

    This demonstrates pytest parametrization best practice for testing
    multiple scenarios with the same test logic. Using parametrization
    eliminates code duplication and makes it easy to add more test cases.

    Runs 3 test cases:
    - Test 4/6: 50MB file  (Good for quick validation)
    - Test 5/6: 100MB file (Standard USB 3.0 test size)
    - Test 6/6: 200MB file (Extended test for sustained performance)

    NOTE: All parametrized tests will run even if one fails, to gather
    complete performance data across different file sizes.

    Args:
        writable_usb_path: Fixture providing validated writable USB path
        size_mb: Size of test file in MB (from parametrize)
        expected_min_speed: Minimum expected speed in MB/s (from parametrize)

    Environment Variables:
        USB_TEST_PATH: Override default USB mount path
    """
    logger.info(f"Testing {size_mb}MB write to {writable_usb_path}")

    # Perform the speed test
    speed = write_test_file(writable_usb_path, size_mb)
    # Track speed for final summary
    USB_SPEEDS.append(speed)
    # Assert speed meets minimum requirement
    assert speed >= expected_min_speed, (
        f"USB write speed {speed:.2f} MB/s is below "
        f"expected minimum of {expected_min_speed} MB/s for {size_mb}MB file. "
        f"USB drive may be USB 2.0 or faulty. USB 3.0 should achieve 50 ~ 100+ MB/s."
    )

    logger.info(f"✓ {size_mb}MB speed test passed ({speed:.2f} MB/s)")
