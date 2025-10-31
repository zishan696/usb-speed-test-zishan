#!/usr/bin/env python3
"""
USB Auto-Detection Demo

Demonstrates automatic USB drive detection across all platforms.
Run this to see what USB drives are detected on your system.
"""

import os
import sys
import subprocess
from usb_detector import (
    get_os_type,
    detect_usb_drives,
    get_first_usb_drive,
    print_usb_info,
    select_usb_drive
)


def main():
    """Main demo function."""
    print("=" * 70)
    print("USB Auto-Detection Demo")
    print("=" * 70)

    # Show detailed USB info
    print_usb_info()

    drives = detect_usb_drives()

    if drives:
        # Ask user to select a USB drive
        print("\n" + "=" * 70)
        print("🎯 USB Drive Selection")
        print("=" * 70)

        selected_drive = None

        if len(drives) == 1:
            # Only one drive, auto-select
            selected_drive = drives[0]['path']
            print(f"\n✅ Only one USB drive detected: {drives[0]['name']}")
            print(f"   Path: {selected_drive}")
            print(f"   Auto-selected for testing.\n")
        else:
            # Multiple drives, let user choose
            print(f"\nPlease select which USB drive you want to test:\n")
            for i, drive in enumerate(drives, 1):
                writable = "✅ Writable" if os.access(drive['path'], os.W_OK) else "❌ Read-only"
                print(f"  {i}. {drive['name']}")
                print(f"     Path: {drive['path']}")
                print(f"     Status: {writable}")
                print()

            # Get user selection
            while True:
                try:
                    choice = input(f"Enter your choice (1-{len(drives)}) or press Enter for #1: ").strip()

                    if not choice:
                        # Default to first drive
                        selected_drive = drives[0]['path']
                        print(f"✅ Selected: {drives[0]['name']} ({selected_drive})\n")
                        break

                    idx = int(choice) - 1
                    if 0 <= idx < len(drives):
                        selected_drive = drives[idx]['path']
                        print(f"✅ Selected: {drives[idx]['name']} ({selected_drive})\n")
                        break
                    else:
                        print(f"❌ Invalid choice. Please enter a number between 1 and {len(drives)}")
                except ValueError:
                    print(f"❌ Invalid input. Please enter a number between 1 and {len(drives)}")
                except KeyboardInterrupt:
                    print("\n\n⚠️  Selection cancelled by user")
                    selected_drive = None
                    break

        # Now ask if user wants to run the full test suite on selected drive
        if selected_drive:
            try:
                response = input("Would you like to run the USB speed test suite on the selected drive? (y/n): ").lower()

                if response == 'y':
                    # Ask user to select test mode
                    print("\n" + "=" * 70)
                    print("🎯 Select Test Mode")
                    print("=" * 70)
                    print("\nAvailable test modes:")
                    print("  1. Simple      - Basic verbose output only")
                    print("  2. Standard    - Verbose with live output (recommended)")
                    print("  3. Debug       - Detailed debugging with full tracebacks")
                    print("  4. Quick       - Stop on first failure (fast feedback)")
                    print("  5. Quiet       - Minimal output, results only")
                    print("  6. Full/All    - Maximum verbosity and details")
                    print()

                    # Define pytest options for each mode
                    test_modes = {
                        '1': {
                            'name': 'Simple',
                            'args': ['-v'],
                            'desc': 'Basic verbose output'
                        },
                        '2': {
                            'name': 'Standard',
                            'args': ['-v', '-s'],
                            'desc': 'Verbose with live output'
                        },
                        '3': {
                            'name': 'Debug',
                            'args': ['-v', '-s', '--tb=long', '--log-cli-level=DEBUG'],
                            'desc': 'Detailed debugging mode'
                        },
                        '4': {
                            'name': 'Quick',
                            'args': ['-v', '-x'],
                            'desc': 'Stop on first failure'
                        },
                        '5': {
                            'name': 'Quiet',
                            'args': ['-q'],
                            'desc': 'Minimal output'
                        },
                        '6': {
                            'name': 'Full',
                            'args': ['-vv', '-s', '--tb=long', '--capture=no'],
                            'desc': 'Maximum verbosity'
                        }
                    }

                    # Get user's mode selection
                    mode_choice = '2'  # Default to Standard
                    try:
                        user_input = input(f"Enter your choice (1-6) or press Enter for Standard mode: ").strip()
                        if user_input and user_input in test_modes:
                            mode_choice = user_input
                        elif user_input and user_input not in test_modes:
                            print(f"⚠️  Invalid choice, using Standard mode")
                    except KeyboardInterrupt:
                        print("\n\n⚠️  Test cancelled by user")
                        return 0

                    selected_mode = test_modes[mode_choice]

                    print("\n" + "=" * 70)
                    print("🏁 Starting Full USB Speed Test Suite")
                    print("=" * 70)
                    print(f"\n📍 Selected Drive: {selected_drive}")
                    print(f"🔧 Test Mode: {selected_mode['name']} ({selected_mode['desc']})")
                    print("📊 Running comprehensive tests (this will take 30-60 seconds)...\n")

                    # Check if drive is writable first
                    if not os.access(selected_drive, os.W_OK):
                        print(f"❌ Cannot run test - {selected_drive} is not writable")
                        print("   Check permissions or try a different drive.")
                        return 1

                    # Set environment variable and run pytest
                    env = os.environ.copy()
                    env['USB_TEST_PATH'] = selected_drive

                    try:
                        # Build pytest command with selected mode
                        pytest_cmd = [sys.executable, '-m', 'pytest', 'test_usb_improved.py'] + selected_mode['args']
                        
                        # Run pytest with the selected USB path and mode
                        result = subprocess.run(
                            pytest_cmd,
                            env=env,
                            check=False
                        )

                        print("\n" + "=" * 70)
                        if result.returncode == 0:
                            print("✅ All tests passed!")
                            print(f"   USB drive {selected_drive} meets USB 3.0 requirements")
                        else:
                            print("⚠️  Some tests failed")
                            print("   Check the output above for details")
                        print("=" * 70 + "\n")

                        return result.returncode

                    except FileNotFoundError:
                        print("\n❌ Error: pytest not found")
                        print("   Please install pytest: pip install pytest")
                        return 1
                    except Exception as e:
                        print(f"\n❌ Error running tests: {e}")
                        return 1
                else:
                    print("\n✅ Test skipped by user")

            except KeyboardInterrupt:
                print("\n\n⚠️  Test cancelled by user")
    else:
        print("\n❌ No USB drives detected")
        print("   Please connect a USB drive and run this demo again.\n")

        # Show how to manually configure
        print("💡 Manual Configuration:")
        print("   You can manually specify a USB path using environment variables:\n")

        os_type = get_os_type()
        if os_type == 'Windows':
            print("   Windows PowerShell:")
            print('   $env:USB_TEST_PATH = "E:\\"')
        else:
            print("   Linux/macOS:")
            print('   export USB_TEST_PATH="/path/to/usb"')

    print("\n" + "=" * 70)
    print("📚 Next Steps")
    print("=" * 70)
    print("\nTo run the full test suite:")
    print("  python -m pytest test_usb_auto.py -v -s")
    print("\nTo see this demo again:")
    print("  python demo_auto_detection.py")
    print("\nFor detailed documentation:")
    print("  Read AUTO_DETECTION_GUIDE.md")
    print("=" * 70 + "\n")

    return 0 if drives else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
