"""
USB Drive Detection Module - Cross-Platform

Automatically detects USB drives on Windows, Linux, and macOS.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict


def get_os_type() -> str:
    """
    Detect the operating system.
    
    Returns:
        str: 'Windows', 'Linux', or 'Darwin' (macOS)
    """
    return platform.system()


def get_windows_usb_drives() -> List[Dict[str, str]]:
    """
    Detect USB drives on Windows.
    
    Returns:
        List[Dict[str, str]]: List of USB drives with path and name
    """
    usb_drives = []
    detected_paths = set()
    
    try:
        # Try using wmic for removable drives (DriveType=2)
        result = subprocess.run(
            ['wmic', 'logicaldisk', 'where', 'drivetype=2', 'get', 'deviceid,volumename'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if parts:
                        drive_letter = parts[0]
                        volume_name = ' '.join(parts[1:]) if len(parts) > 1 else "USB Drive"
                        drive_path = drive_letter + '\\'
                        usb_drives.append({
                            'path': drive_path,
                            'name': volume_name or "USB Drive"
                        })
                        detected_paths.add(drive_path)
        
        # Also check DriveType=3 (local disk) for USB drives detected as local
        # Some large USB drives or external HDDs are detected as DriveType=3
        result2 = subprocess.run(
            ['wmic', 'logicaldisk', 'where', 'drivetype=3', 'get', 'deviceid,volumename'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result2.returncode == 0:
            lines = result2.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                line = line.strip()
                if line:
                    parts = line.split()
                    if parts:
                        drive_letter = parts[0]
                        # Only add if it's not C: (system drive) and not already detected
                        if drive_letter.upper() not in ['C:', 'C'] and drive_letter + '\\' not in detected_paths:
                            volume_name = ' '.join(parts[1:]) if len(parts) > 1 else f"Drive {drive_letter}"
                            drive_path = drive_letter + '\\'
                            usb_drives.append({
                                'path': drive_path,
                                'name': volume_name or f"Drive {drive_letter}"
                            })
                            detected_paths.add(drive_path)
                            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    # Fallback: Check all drive letters D-Z if no drives detected yet
    if not usb_drives:
        for letter in 'DEFGHIJKLMNOPQRSTUVWXYZ':
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                try:
                    # Try to access the drive to verify it's readable
                    os.listdir(drive_path)
                    usb_drives.append({
                        'path': drive_path,
                        'name': f"Drive {letter}"
                    })
                except (PermissionError, OSError):
                    continue
    
    return usb_drives


def get_linux_usb_drives() -> List[Dict[str, str]]:
    """
    Detect USB drives on Linux.
    
    Returns:
        List[Dict[str, str]]: List of USB drives with path and name
    """
    usb_drives = []
    username = os.getenv('USER', 'user')
    
    # Common mount locations for USB drives on Linux
    mount_locations = [
        f"/media/{username}/",
        f"/run/media/{username}/",
        "/mnt/",
        "/media/",
    ]
    
    for mount_base in mount_locations:
        if os.path.exists(mount_base):
            try:
                for entry in os.listdir(mount_base):
                    full_path = os.path.join(mount_base, entry)
                    if os.path.ismount(full_path) and os.access(full_path, os.R_OK):
                        usb_drives.append({
                            'path': full_path,
                            'name': entry
                        })
            except (PermissionError, OSError):
                continue
    
    # Also check lsblk output for removable devices
    try:
        result = subprocess.run(
            ['lsblk', '-o', 'NAME,MOUNTPOINT,RM,TYPE', '-n'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) >= 4 and parts[2] == '1' and parts[3] == 'part':
                    # Removable partition with mount point
                    if len(parts) > 1 and parts[1] != '' and parts[1] not in [d['path'] for d in usb_drives]:
                        mount_point = ' '.join(parts[1:-2])
                        if os.path.exists(mount_point):
                            usb_drives.append({
                                'path': mount_point,
                                'name': os.path.basename(mount_point)
                            })
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    # Remove duplicates
    seen = set()
    unique_drives = []
    for drive in usb_drives:
        if drive['path'] not in seen:
            seen.add(drive['path'])
            unique_drives.append(drive)
    
    return unique_drives


def get_macos_usb_drives() -> List[Dict[str, str]]:
    """
    Detect USB drives on macOS.
    
    Returns:
        List[Dict[str, str]]: List of USB drives with path and name
    """
    usb_drives = []
    volumes_path = Path("/Volumes")
    
    if volumes_path.exists():
        for volume in volumes_path.iterdir():
            # Skip Macintosh HD and other system volumes
            if volume.name not in ['Macintosh HD', 'Macintosh HD - Data', 'Data']:
                try:
                    # Check if accessible
                    if volume.is_dir() and os.access(volume, os.R_OK):
                        usb_drives.append({
                            'path': str(volume),
                            'name': volume.name
                        })
                except (PermissionError, OSError):
                    continue
    
    # Use diskutil to get more detailed info about removable media
    try:
        result = subprocess.run(
            ['diskutil', 'list', '-plist'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Alternative: Use diskutil info to check if removable
        result = subprocess.run(
            ['diskutil', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse diskutil output for external drives
            # This is a simplified approach
            pass
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    
    return usb_drives


def detect_usb_drives() -> List[Dict[str, str]]:
    """
    Automatically detect USB drives on any operating system.
    
    Returns:
        List[Dict[str, str]]: List of dictionaries with 'path' and 'name' keys
        
    Example:
        [
            {'path': 'E:\\', 'name': 'USB_DRIVE'},
            {'path': 'F:\\', 'name': 'BACKUP'},
        ]
    """
    os_type = get_os_type()
    
    if os_type == 'Windows':
        return get_windows_usb_drives()
    elif os_type == 'Linux':
        return get_linux_usb_drives()
    elif os_type == 'Darwin':  # macOS
        return get_macos_usb_drives()
    else:
        return []


def get_first_usb_drive() -> Optional[str]:
    """
    Get the first detected USB drive path.
    
    Returns:
        Optional[str]: Path to first USB drive, or None if not found
    """
    drives = detect_usb_drives()
    return drives[0]['path'] if drives else None


def select_usb_drive(interactive: bool = True) -> Optional[str]:
    """
    Detect and optionally let user select a USB drive.
    
    Args:
        interactive (bool): If True, prompt user to select from multiple drives
        
    Returns:
        Optional[str]: Selected USB drive path, or None if not found
    """
    drives = detect_usb_drives()
    
    if not drives:
        return None
    
    if len(drives) == 1:
        return drives[0]['path']
    
    if not interactive:
        # Return first drive if not interactive
        return drives[0]['path']
    
    # Interactive mode: let user select
    print("\n🔍 Multiple USB drives detected:")
    for i, drive in enumerate(drives, 1):
        print(f"  {i}. {drive['name']} ({drive['path']})")
    
    while True:
        try:
            choice = input(f"\nSelect drive (1-{len(drives)}) or press Enter for first: ").strip()
            if not choice:
                return drives[0]['path']
            
            idx = int(choice) - 1
            if 0 <= idx < len(drives):
                return drives[idx]['path']
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(drives)}")
        except (ValueError, KeyboardInterrupt):
            return drives[0]['path']


def print_usb_info() -> None:
    """Print information about detected USB drives."""
    os_type = get_os_type()
    print(f"\n🖥️  Operating System: {os_type}")
    print(f"🔍 Scanning for USB drives...\n")
    
    drives = detect_usb_drives()
    
    if drives:
        print(f"✅ Found {len(drives)} USB drive(s):\n")
        for i, drive in enumerate(drives, 1):
            writable = "✅ Writable" if os.access(drive['path'], os.W_OK) else "❌ Read-only"
            print(f"  {i}. {drive['name']}")
            print(f"     Path: {drive['path']}")
            print(f"     Status: {writable}")
            
            # Get free space if available
            try:
                if hasattr(os, 'statvfs'):
                    stat = os.statvfs(drive['path'])
                    free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
                    total_mb = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
                    print(f"     Space: {free_mb:.1f} MB free / {total_mb:.1f} MB total")
                elif os_type == 'Windows':
                    import shutil
                    total, used, free = shutil.disk_usage(drive['path'])
                    print(f"     Space: {free / (1024**2):.1f} MB free / {total / (1024**2):.1f} MB total")
            except Exception:
                pass
            
            print()
    else:
        print("❌ No USB drives detected.")
        print("\n💡 Troubleshooting:")
        if os_type == 'Windows':
            print("   - Make sure USB drive is properly connected")
            print("   - Check if drive appears in File Explorer")
            print("   - Try a different USB port")
        elif os_type == 'Linux':
            print("   - Make sure USB drive is mounted")
            print("   - Run 'lsblk' to see all block devices")
            print("   - Check /media/$USER/ for mounted drives")
        elif os_type == 'Darwin':
            print("   - Make sure USB drive is mounted")
            print("   - Check Finder > Locations for USB drive")
            print("   - Try ejecting and reconnecting")


if __name__ == '__main__':
    # Demo: Show detected USB drives
    print_usb_info()

