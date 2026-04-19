#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions - Full Version Build Script
Includes Node.js runtime
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
    node_dir = repo_root / "node"
    output_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    
    print("=" * 50)
    print("  WoWFontsHappy - Full Version Build")
    print("  (Includes Node.js runtime)")
    print("=" * 50)
    
    # Check Node.js directory
    if not node_dir.exists():
        print(f"[ERROR] Node.js directory not found: {node_dir}")
        print("Please download and extract Node.js to ./node")
        return 1
    
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

# Get resource path
if hasattr(sys, '_MEIPASS'):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).parent

bundle_dir = base / "bundle"
app_dir = bundle_dir / "app"
node_dir = bundle_dir / "node"
node_exe = node_dir / "node.exe"
server_js = app_dir / "server.js"
public_dir = app_dir / "public"
index_html = public_dir / "index.html"

if not index_html.exists():
    print("[ERROR] index.html not found")
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

# Set environment
env = os.environ.copy()
env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
env["NODE_ENV"] = "production"
env["PUBLIC_DIR"] = str(public_dir)

# Start server
process = subprocess.Popen(
    [str(node_exe), str(server_js)],
    cwd=app_dir,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace'
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
        
        print("\nPreparing resources...")
        
        # Prepare bundle
        bundle = temp_dir / "bundle"
        # Copy app directory, exclude unnecessary files
        def ignore_app(dir, files):
            return ['.git', '.github', 'dist', 'build', 'node_modules', '.gitignore', 'README.md']
        shutil.copytree(app_dir, bundle / "app", ignore=ignore_app)
        # Copy node directory
        shutil.copytree(node_dir, bundle / "node", 
                       ignore=shutil.ignore_patterns('*.pdb', 'CHANGELOG*', 'LICENSE', 'README*'))
        # Install production dependencies in bundle/app
        print("[INSTALL] npm production dependencies...")
        npm_result = subprocess.run(
            [str(node_dir / "npm.cmd"), "ci", "--production"],
            cwd=bundle / "app",
            capture_output=True,
            text=True
        )
        if npm_result.returncode != 0:
            print(f"[WARN] npm install failed: {npm_result.stderr}")
        else:
            print("[OK] npm dependencies installed")
        
        print("Building EXE...")
        
        # Clean build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)
        
        # PyInstaller arguments
        bundle_str = str(bundle).replace('\\', '/')
        launcher_str = str(launcher_path).replace('\\', '/')
        
        args = [
            sys.executable, "-m", "PyInstaller",
            "--name", "WoWFontsHappy-Full",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            "--distpath", str(output_dir),
            "--workpath", str(build_dir),
            "--add-data", f"{bundle_str};bundle",
            launcher_str
        ]
        
        subprocess.run(args, check=True)
        print("[OK] Full version build complete")
        
        # Show file size
        exe_path = output_dir / "WoWFontsHappy-Full.exe"
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"   File: {exe_path}")
            print(f"   Size: {size:.1f} MB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
