#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions - Mini Version Build Script
Does not include Node.js runtime (requires Node.js installed)
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


class Builder:
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent.parent.absolute()
        # GitHub Actions 中代码在仓库根目录，本地开发时在 WOWFontsHappy 子目录
        if (self.repo_root / "server.js").exists():
            self.source_dir = self.repo_root
        else:
            self.source_dir = self.repo_root / "WOWFontsHappy"
        self.output_dir = self.repo_root / "dist"
        self.build_dir = self.repo_root / "build"
        self.temp_dir = None
        
    def prepare_app(self):
        """准备应用文件"""
        print("=" * 50)
        print("Preparing application...")
        print("=" * 50)
        
        self.temp_dir = Path(tempfile.mkdtemp())
        app_dir = self.temp_dir / "app"
        
        # 复制应用文件
        shutil.copytree(
            self.source_dir, 
            app_dir, 
            ignore=shutil.ignore_patterns(
                'node_modules', '.git', '*.log', 'dist', 'build', '.github'
            )
        )
        print(f"[OK] Copied app to: {app_dir}")
        
        # 安装生产依赖
        print("[Install] npm production dependencies...")
        npm_result = subprocess.run(
            ["npm", "ci", "--production"],
            cwd=app_dir,
            capture_output=True,
            text=True
        )
        if npm_result.returncode != 0:
            print(f"[WARN] npm install output: {npm_result.stderr}")
        else:
            print("[OK] npm dependencies installed")
        
        return app_dir
    
    def create_launcher(self, app_dir):
        """创建启动器"""
        launcher_code = '''
import os, sys, subprocess, time
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
    print("[ERROR] index.html not found, please rebuild")
    input("Press Enter to exit...")
    sys.exit(1)

# Check Node.js
try:
    subprocess.run(["node", "--version"], capture_output=True, check=True)
except:
    print("[ERROR] Node.js not found. Please install Node.js first.")
    print("       Download: https://nodejs.org/")
    input("Press Enter to exit...")
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
        launcher_path = self.temp_dir / "launcher.py"
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)
        return launcher_path
    
    def build(self, launcher_path, app_dir):
        """构建 EXE"""
        print("\n" + "=" * 50)
        print("Building EXE...")
        print("=" * 50)
        
        # 清理构建目录
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # PyInstaller 参数
        app_dir_str = str(app_dir).replace('\\', '/')
        launcher_str = str(launcher_path).replace('\\', '/')
        icon_path = str(self.source_dir / "FontsHappy.ico").replace('\\', '/')
        
        args = [
            sys.executable, "-m", "PyInstaller",
            "--name", "魔兽字体好开心-精简版",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            "--icon", icon_path,
            "--distpath", str(self.output_dir),
            "--workpath", str(self.build_dir),
            "--add-data", f"{app_dir_str};app",
            launcher_str
        ]
        
        subprocess.run(args, check=True)
        print("[OK] Build complete")
        
        # 显示文件大小
        exe_path = self.output_dir / "魔兽字体好开心-精简版.exe"
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"   File: {exe_path}")
            print(f"   Size: {size:.1f} MB")
        
        return True
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        # 清理 spec 文件
        spec = self.repo_root / "魔兽字体好开心-精简版.spec"
        if spec.exists():
            spec.unlink()
    
    def run(self):
        print("\n" + "=" * 50)
        print("  WoWFontsHappy - Mini Version Build")
        print("  (Requires Node.js installed)")
        print("=" * 50 + "\n")
        
        try:
            app_dir = self.prepare_app()
            launcher_path = self.create_launcher(app_dir)
            self.build(launcher_path, app_dir)
            return 0
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            self.cleanup()


def main():
    builder = Builder()
    return builder.run()


if __name__ == "__main__":
    sys.exit(main())
