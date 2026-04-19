#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions - Mini Version Build Script
Does not include Node.js runtime
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    # Path settings
    repo_root = Path(__file__).parent.parent.parent
    app_dir = repo_root
    output_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    
    print("=" * 50)
    print("  WoWFontsHappy - Mini Version Build")
    print("  (Requires Node.js installed)")
    print("=" * 50)
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        
        # Create launcher
        launcher_code = '''
import os
import sys
import subprocess
from pathlib import Path

# Get app path
if hasattr(sys, '_MEIPASS'):
    app_dir = Path(sys._MEIPASS) / "app"
else:
    app_dir = Path(__file__).parent / "app"

server_js = app_dir / "server.js"
public_dir = app_dir / "public"
index_html = public_dir / "index.html"

if not index_html.exists():
    print("[ERROR] index.html not found")
    sys.exit(1)

# Check Node.js
try:
    subprocess.run(["node", "--version"], capture_output=True, check=True)
except:
    print("[ERROR] Node.js not found. Please install Node.js first.")
    print("       Download: https://nodejs.org/")
    sys.exit(1)

# Kill process using port 3456
print("[CHECK] Checking port 3456...")
try:
    result = subprocess.run(
        ['netstat', '-ano', '|', 'findstr', ':3456'],
        capture_output=True, text=True, shell=True
    )
    if ':3456' in result.stdout:
        print("[WARN] Port 3456 in use, terminating process...")
        for line in result.stdout.strip().splitlines():
            if ':3456' in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        print(f"[OK] Terminated PID: {pid}")
                    except:
                        pass
        import time
        time.sleep(1)
    else:
        print("[OK] Port 3456 is free")
except Exception as e:
    print(f"[WARN] Error checking port: {e}")

print("=" * 50)
print("  WoWFontsHappy")
print("=" * 50)
print("  URL: http://localhost:3456")
print("  Press Ctrl+C to stop")
print("=" * 50)
print()

# Set environment variables
env = os.environ.copy()
env["PUBLIC_DIR"] = str(public_dir)

# Start server
process = subprocess.Popen(
    f'node "{server_js}"',
    cwd=app_dir,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace',
    shell=True
)

# Read output
try:
    for line in process.stdout:
        print(line, end='')
except KeyboardInterrupt:
    print("")
    print("Stopping server...")
except Exception as e:
    print(f"[ERROR] Error reading output: {e}")

# Terminate process
if process.poll() is None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except:
        process.kill()
'''
        
        launcher_path = temp_dir / "launcher.py"
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)
        
        print("\nBuilding EXE...")
        
        # Clean build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)
        
        # PyInstaller arguments
        app_dir_str = str(app_dir).replace('\\', '/')
        launcher_str = str(launcher_path).replace('\\', '/')
        
        args = [
            sys.executable, "-m", "PyInstaller",
            "--name", "WoWFontsHappy-Mini",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            "--distpath", str(output_dir),
            "--workpath", str(build_dir),
            "--add-data", f"{app_dir_str};app",
            launcher_str
        ]
        
        subprocess.run(args, check=True)
        print("[OK] Mini version build complete")
        
        # Show file size
        exe_path = output_dir / "WoWFontsHappy-Mini.exe"
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"   File: {exe_path}")
            print(f"   Size: {size:.1f} MB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
