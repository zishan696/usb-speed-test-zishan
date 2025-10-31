# ⚡ USB 3.0 Speed Test Documentation

**Cross-platform USB 3.0 speed testing framework with intelligent fail-fast behavior and automatic drive detection feature.**

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![pytest](https://img.shields.io/badge/pytest-8.0+-green.svg)](https://docs.pytest.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Code Style](https://img.shields.io/badge/code%20style-production-orange.svg)](https://github.com)

---

## 📋 Overview

This project demonstrates production-level Python testing practices through a real-world USB speed verification tool. It combines modern pytest features, cross-platform compatibility, and intelligent test orchestration to create a robust hardware testing framework.

**Key Differentiators:**
- ✅ Intelligent conditional fail-fast (pre-conditions vs performance tests)
- ✅ Can be used with the Automatic USB drive detection across all major OS platforms
- ✅ Interactive test mode selection (Simple, Debug, Quick, etc.)
- ✅ Zero-configuration setup from the get-go with graceful fallbacks
- ✅ Production-ready error handling and logging

---

## ✨ Features

### 🎯 Smart Test Orchestration
- **Conditional Fail-Fast**: Pre-condition tests stop immediately on failure, but performance tests run completely for full data collection
- **Custom pytest Hooks**: Advanced `conftest.py` with test reordering (pre-conditions first, then performance tests) and intelligent skipping
- **Test Markers**: Organized tests with `@pytest.mark.precondition` and `@pytest.mark.performance`

### 🔌 Automatic USB Detection
- **Platform-Aware**: Uses `wmic` (Windows), `lsblk` (Linux), `diskutil` (macOS)
- **Intelligent Fallback**: Environment variable override for manual configuration
- **Interactive Selection**: User-friendly drive picker when multiple USB devices detected

### 📊 Comprehensive Testing
- **Parametrized Tests**: Multiple file sizes (50MB, 100MB, 200MB)
- **Edge Case Coverage**: Invalid inputs, insufficient space, path validation
- **Performance Summary**: Detailed speed metrics (average, min, max)

### 🎮 Multiple Test Modes
- **Simple**: Clean verbose output (`-v`)
- **Standard**: Live output with real-time progress (`-v -s`)
- **Debug**: Full tracebacks and debug logs (`-v -s --tb=long --log-cli-level=DEBUG`)
- **Quick**: Stop on first failure (`-v -x`)
- **Quiet**: Minimal output (`-q`)
- **Full**: Maximum verbosity (`-vv -s --tb=long`)

---

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.7 or higher
python --version

# Install pytest
pip install pytest
```

### Basic Usage

**1. Interactive Demo (Recommended for First-Time Users)**
```bash
python usb_speed_test_launcher.py
```
This will:
- Detect your operating system
- Find all connected USB drives
- Let you select which drive to test
- Choose test mode (Simple, Debug, etc.)
- Run comprehensive speed tests

**2. Direct Test Execution**
```bash
# If USB drive is selected or added in the test_usb_improved.py file (DEFAULT_USB_PATH)
python -m pytest test_usb_improved.py -v -s

# Specify USB path manually
# Windows, Find the appropriate path using `Get-PSDrive -PSProvider FileSystem`
$env:USB_TEST_PATH = "E:\"
python -m pytest test_usb_improved.py -v -s

# Linux/macOS
export USB_TEST_PATH="/media/<user>/USB_DRIVE"
python -m pytest test_usb_improved.py -v -s
```

---

## 📁 Project Structure

```
usb-speed-test-zishan/
├── test_usb_improved.py       # Main test suite with fixtures & parametrization
├── conftest.py                # pytest hooks for intelligent test orchestration
├── usb_detector.py            # Cross-platform USB auto-detection module
├── usb_speed_test_launcher.py # Interactive demo with drive selection and run USB speed test in a complete package
├── pytest.ini                 # pytest configuration & custom markers
├── .gitignore                 # Git ignore patterns
└── README.md                  # This file
```

### File Responsibilities

| File | Purpose | Key Technologies |
|------|---------|------------------|
| `test_usb_improved.py` | Core test suite | pytest fixtures, parametrization, logging |
| `conftest.py` | Test orchestration | pytest hooks, custom markers, conditional fail-fast |
| `usb_detector.py` | Platform detection | subprocess, platform-specific commands |
| `usb_speed_test_launcher.py` | User interface | Interactive selection, subprocess management |
| `pytest.ini` | Test configuration | Markers, verbosity, traceback settings |

---

## 🧪 Test Architecture

### Test Execution Flow

```
┌─────────────────────────────────────┐
│  pytest_collection_modifyitems()    │  ← Reorder tests
│  (Pre-conditions → Performance)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  SECTION 1: Pre-condition Checks    │
│  ├─ test_usb_path_writable          │
│  ├─ test_usb_sufficient_space       │  ← Stop if any fails
│  └─ test_invalid_size_raises_error  │
└──────────────┬──────────────────────┘
               │ (all passed)
               ▼
┌─────────────────────────────────────┐
│  SECTION 2: Performance Tests       │
│  ├─ test_usb_speed[50MB]            │
│  ├─ test_usb_speed[100MB]           │  ← Run all, collect data
│  └─ test_usb_speed[200MB]           │
└─────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  pytest_terminal_summary()          │  ← Custom summary
│  (Average speed, min/max, status)   │
└─────────────────────────────────────┘
```

### Intelligent Fail-Fast Logic

**Why Conditional?**
- **Pre-condition failures**: Indicate setup issues (USB not found, not writable, insufficient space) → Stop immediately for fast feedback
- **Performance test failures**: USB might be slow but still gather all data points → Run all tests for complete analysis

**Implementation**: Custom pytest hooks in `conftest.py`
- `pytest_collection_modifyitems`: Reorders tests by marker
- `pytest_runtest_makereport`: Tracks pre-condition failures
- `pytest_runtest_setup`: Skips performance tests if pre-condition failed
- `pytest_terminal_summary`: Custom colored output with speed summary

---

## 📊 Expected Output

### Successful Test Run
```
======================================================================
TEST EXECUTION ORDER:
======================================================================
  Pre-conditions (3): ['test_usb_path_writable', 'test_usb_sufficient_space', 'test_invalid_size_raises_error']
  Performance (3): ['test_usb_speed_parametrized[50-50.0]', 'test_usb_speed_parametrized[100-50.0]', 'test_usb_speed_parametrized[200-50.0]']
======================================================================

test_usb_improved.py::test_usb_path_writable PASSED
test_usb_improved.py::test_usb_sufficient_space PASSED
test_usb_improved.py::test_invalid_size_raises_error PASSED

======================================================================
  ✅ All pre-condition checks passed!
  🚀 Starting USB performance tests...
======================================================================

======================================================================
  Testing: 50MB file write to H:\
======================================================================
  ...
======================================================================
  📊 USB Speed Test Result: 50MB file
  ──────────────────────────────────────────────────────────────────
  ⚡ Write Speed:    283.84 MB/s
  📋 Required Min:   50.00 MB/s
  ──────────────────────────────────────────────────────────────────
  ✅ Status: PASS (Speed is sufficient)
======================================================================

test_usb_improved.py::test_usb_speed_parametrized[50-50.0] PASSED
test_usb_improved.py::test_usb_speed_parametrized[100-50.0] PASSED
test_usb_improved.py::test_usb_speed_parametrized[200-50.0] PASSED

================================================== ALL TESTS PASSED ==================================================
✓ USB drive meets all requirements!
Average write speed was 293.53 MB/s
================================================== 6 passed in 1.33s ==================================================
```

### Pre-condition Failure Example
```
test_usb_improved.py::test_usb_path_writable FAILED

⚠️  Pre-condition test 'test_usb_path_writable' failed!
⚠️  Skipping all remaining tests...

================================================== PRE-CONDITION FAILURE ==================================================
Pre-condition test 'test_usb_path_writable' failed.
Performance tests were skipped to save time.
Fix the pre-condition issue and re-run tests.
```

---

## 🎮 Usage Examples

### Example 1: Interactive Demo (Best for Beginners)
```bash
python usb_speed_test_launcher.py
```
**What it does:**
1. Scans for USB drives
2. Displays all detected drives with details
3. Lets you select which drive to test
4. Choose test mode (Simple/Debug/Quick/etc.)
5. Runs full test suite

### Example 2: Automated Testing
```bash
# Test first USB drive
python -m pytest test_usb_improved.py -v -s
```

### Example 3: Manual Path Override
```bash
# Windows PowerShell
$env:USB_TEST_PATH = "F:\"
python -m pytest test_usb_improved.py -v -s

# Linux/macOS Terminal
export USB_TEST_PATH="/Volumes/MY_USB"
python -m pytest test_usb_improved.py -v -s
```

### Example 4: Specific Test Selection
```bash
# Run only pre-condition tests
python -m pytest test_usb_improved.py -v -m precondition

# Run only performance tests
python -m pytest test_usb_improved.py -v -m performance

# Run specific parametrized test
python -m pytest test_usb_improved.py::test_usb_speed_parametrized[100-50.0] -v -s
```

### Example 5: Different Test Modes
```bash
# Quick mode - stop on first failure
python -m pytest test_usb_improved.py -v -x

# Quiet mode - minimal output
python -m pytest test_usb_improved.py -q

# Debug mode - full details
python -m pytest test_usb_improved.py -v -s --tb=long --log-cli-level=DEBUG
```

### Example 6: Using Detection Module Programmatically
```python
from usb_detector import detect_usb_drives, get_first_usb_drive, print_usb_info

# Get all USB drives
drives = detect_usb_drives()
for drive in drives:
    print(f"Found: {drive['name']} at {drive['path']}")

# Get first writable USB
usb_path = get_first_usb_drive()
if usb_path:
    print(f"Using: {usb_path}")

# Display detailed information
print_usb_info()
```

---

## 🔧 Configuration

### Environment Variables
```bash
USB_TEST_PATH       # Override auto-detection with specific path
```

### Constants in `test_usb_improved.py`
```python
MIN_SPEED_MBPS = 50.0            # Minimum required speed (USB 3.0)
TEST_SIZES_MB = [50, 100, 200]   # Parametrized test sizes
SPACE_BUFFER_MULTIPLIER = 1.5    # 50% safety buffer for space checks
MIN_FILE_SIZE_MB = 1             # Minimum file size (prevents cache issues)
CHUNK_SIZE_BYTES = 1 MB          # Write chunk size
PROGRESS_LOG_INTERVAL = 10       # Log every N chunks
```

### pytest Markers (in `pytest.ini`)
```ini
[pytest]
markers =
    usb: USB-related tests
    precondition: Pre-condition checks (fail-fast)
    performance: Performance tests (run all)
```

---

## 🖥️ Platform Support

| Platform | Detection Method | Typical USB Paths | Status |
|----------|------------------|-------------------|--------|
| **Windows** | `wmic logicaldisk` | `E:\`, `F:\`, `G:\` | ✅ Tested |
| **Linux** | `lsblk` + mount check | `/media/user/USB`, `/mnt/usb` | ✅ Tested |
| **macOS** | `diskutil list` | `/Volumes/USB_NAME` | ✅ Tested |

### Platform-Specific Notes

**Windows:**
- Detects removable drives (DriveType=2)
- Fallback to drive letter scan (A-Z)
- Handles both PowerShell and CMD

**Linux:**
- Uses `lsblk` to identify USB devices
- Checks mount points in `/media` and `/mnt`
- Verifies write permissions

**macOS:**
- Scans `/Volumes/` directory
- Uses `diskutil` for detailed info
- NTFS drives may be read-only (need macFUSE)

---

## 🔍 Code Quality Metrics

- **Test Coverage**: 6 comprehensive tests (3 pre-conditions + 3 performance)
- **Lines of Code**: ~800 lines (including documentation)
- **Functions**: 15+ well-documented functions
- **Platform Support**: 3 major operating systems
- **Error Scenarios**: 8+ handled edge cases
- **Documentation**: Extensive inline and external docs

---

## 🐛 Troubleshooting

### No USB Drives Detected

**Check Detection:**
```bash
# Run detection module directly
python usb_detector.py
```

**Windows:**
```powershell
# Verify with these commands on Windows to sees the drive
wmic logicaldisk get deviceid,volumename,drivetype
fsutil fsinfo drives
```

**Linux:**
```bash
# Check mounted drives
lsblk
df -h | grep media
```

**macOS:**
```bash
# List volumes
ls -la /Volumes/
diskutil list
```

### USB Not Writable

**Linux:**
```bash
# Check permissions
ls -ld /media/$USER/USB_DRIVE

# Fix permissions (if needed)
sudo chmod 777 /media/$USER/USB_DRIVE
```

**macOS (NTFS drives):**
```bash
# NTFS is read-only by default on macOS
# Solution 1: Install macFUSE + NTFS-3G
# Solution 2: Reformat USB to exFAT (cross-platform compatible)
```

**Windows:**
- Check physical write-protect switch on USB
- Verify in Properties → Security tab

### Tests Running Too Slowly

**Issue**: Tests take minutes instead of seconds

**Causes & Solutions:**
1. **USB 2.0 drive**: Upgrade to USB 3.0 (blue port)
2. **Fragmented drive**: Format USB drive
3. **Background processes**: Close unnecessary applications
4. **Power management**: Check USB power settings in Device Manager

### Tests Show Suspicious Speeds

**Issue**: Speeds like 2000+ MB/s (unrealistic)

**Cause**: OS caching or filesystem compression

**Solution**: Already handled by:
- Using random data (prevents compression)
- `os.fsync()` to flush OS cache
- Minimum file size of 1MB

---

## 💡 Design Decisions

### Why Random Data?
Non-random data (like `b'X' * 1024`) can be compressed by modern filesystems, giving false high-speed readings. Random data ensures realistic measurements.

### Why Conditional Fail-Fast?
- **Pre-conditions** (USB found, writable, space): Fast failure saves time
- **Performance tests**: Need all data points (50MB, 100MB, 200MB) for trend analysis

### Why 50 MB/s Minimum?
USB 3.0 specification requires minimum 50 MB/s write speed. This distinguishes USB 3.0 from USB 2.0 (max ~35 MB/s).

### Why Multiple File Sizes?
Different file sizes can reveal issues:
- Small files (50MB): Quick verification
- Large files (200MB): Sustained performance, thermal throttling

### Why `os.fsync()`?
Ensures data is actually written to physical disk, not just cached in RAM by the OS.

### Why 1MB Minimum File Size?
Files smaller than 1MB can be entirely cached in RAM, giving misleading "infinite" speed readings.

---

## 📈 Performance Benchmarks

| USB Type | Expected Speed | Test Result |
|----------|---------------|-------------|
| USB 2.0 | 20-35 MB/s | ❌ Fails (too slow) |
| USB 3.0 | 50-100 MB/s | ✅ Passes |
| USB 3.1 Gen 1 | 100-200 MB/s | ✅ Passes (exceeds) |
| USB 3.1 Gen 2 | 200-500+ MB/s | ✅ Passes (exceeds) |

**Test Duration:**
- Pre-conditions: <1 second
- Each performance test: 0.5-3 seconds (depends on USB speed)
- **Total**: 1-10 seconds for complete suite

---

## 🚀 Future Enhancements

- [ ] Read speed testing
- [ ] USB-C / Thunderbolt detection
- [ ] Benchmark database (SQLite)
- [ ] HTML report generation
- [ ] CI/CD integration examples
- [ ] Docker containerization
- [ ] GUI version (tkinter/PyQt/Electron)
- [ ] Multiple simultaneous USB tests

---

## 📚 Learning Resources

If you're reviewing this code for learning, focus on:

1. **`conftest.py`**: Advanced pytest hooks and markers
2. **`usb_detector.py`**: Cross-platform subprocess handling
3. **`test_usb_improved.py`**: Fixtures, parametrization, and production practices
4. **`usb_speed_test_launcher.py`**: User interaction and subprocess integration

---

## 🤝 Contributing

This project demonstrates production-level Python development. Feel free to:
- Fork and adapt for your own use cases
- Study the code structure and patterns
- Use as a reference for pytest best practices
- Extend with additional features

---

## 📜 License

MIT License - Free to use for learning, interviews, or production deployment.

---

## 🌟 Key Takeaways

This project showcases:

✅ **Production-Ready Code**: Error handling, logging, validation, resource cleanup  
✅ **Advanced pytest**: Custom hooks, fixtures, parametrization, markers  
✅ **Cross-Platform Development**: OS abstraction, platform-specific handling  
✅ **Best Practices**: DRY, SOLID, clear documentation, meaningful names  
✅ **Real-World Application**: Solves actual hardware testing needs  
✅ **Interview-Ready**: Well-organized, documented, and demonstrable  

---

## 📞 Quick Reference

```bash
# Interactive demo (easiest)
python usb_speed_test_launcher.py

# Run all tests (USB Path required)
python -m pytest test_usb_improved.py -v -s

# Run with manual path together
USB_TEST_PATH="/path/to/usb" python -m pytest test_usb_improved.py -v -s

# Run specific marker group
python -m pytest test_usb_improved.py -v -m precondition

# Show detected drives
python usb_detector.py

# Quick mode (stop on first failure)
python -m pytest test_usb_improved.py -v -x

# Debug mode (full details)
python -m pytest test_usb_improved.py -v -s --tb=long --log-cli-level=DEBUG
```

---

**Built with ❤️ to demonstrate professional Python testing practices.**

*Thank you!*

