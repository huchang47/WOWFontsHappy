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
import zipfile
import urllib.request
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
        self.node_version = "18.20.4"
        self.node_url = f"https://nodejs.org/dist/v{self.node_version}/node-v{self.node_version}-win-x64.zip"
        
    def download_node(self):
        """下载并解压 Node.js"""
        print("=" * 50)
        print("Preparing Node.js...")
        print("=" * 50)
        
        node_zip = self.repo_root / "node.zip"
        node_dir = self.repo_root / "node"
        
        # 如果已经解压过，直接使用
        if node_dir.exists():
            print(f"[OK] Using existing: {node_dir}")
            return node_dir
        
        # 如果已下载但未解压
        if node_zip.exists():
            print(f"[OK] Using downloaded: {node_zip}")
        else:
            print(f"[Download] Node.js v{self.node_version}...")
            urllib.request.urlretrieve(self.node_url, node_zip)
            print("[OK] Download complete")
        
        print("[Extract] Node.js...")
        with zipfile.ZipFile(node_zip, 'r') as z:
            z.extractall(self.repo_root)
        
        # 重命名为 node
        extracted_dir = self.repo_root / f"node-v{self.node_version}-win-x64"
        if extracted_dir.exists():
            extracted_dir.rename(node_dir)
        
        print(f"[OK] Extracted to: {node_dir}")
        return node_dir
    
    def prepare_app(self):
        """准备应用文件"""
        print("\n" + "=" * 50)
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
    
    def create_launcher(self, app_dir, node_dir):
        """创建启动器"""
        launcher_code = '''
import os, sys, subprocess, time
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
    print("[ERROR] index.html not found, please rebuild")
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

# Set environment
env = os.environ.copy()
env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
env["NODE_ENV"] = "production"
env["PUBLIC_DIR"] = str(public_dir)

print("=" * 50)
print("  WoWFontsHappy")
print("=" * 50)
print("  URL: http://localhost:3456")
print("  Press Ctrl+C to stop")
print("=" * 50)
print()

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
        launcher_path = self.temp_dir / "launcher.py"
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write(launcher_code)
        return launcher_path
    
    def build(self, launcher_path, app_dir, node_dir):
        """构建 EXE"""
        print("\n" + "=" * 50)
        print("Building EXE...")
        print("=" * 50)
        
        # 清理构建目录
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 准备资源
        bundle = self.temp_dir / "bundle"
        shutil.copytree(app_dir, bundle / "app")
        shutil.copytree(
            node_dir, 
            bundle / "node", 
            ignore=shutil.ignore_patterns('*.pdb', 'CHANGELOG*', 'LICENSE', 'README*')
        )
        
        # PyInstaller 参数
        bundle_str = str(bundle).replace('\\', '/')
        launcher_str = str(launcher_path).replace('\\', '/')
        icon_path = str(self.source_dir / "FontsHappy.ico").replace('\\', '/')
        
        args = [
            sys.executable, "-m", "PyInstaller",
            "--name", "魔兽字体好开心-完整版",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            "--icon", icon_path,
            "--distpath", str(self.output_dir),
            "--workpath", str(self.build_dir),
            "--add-data", f"{bundle_str};bundle",
            launcher_str
        ]
        
        subprocess.run(args, check=True)
        print("[OK] Build complete")
        
        # 显示文件大小
        exe_path = self.output_dir / "魔兽字体好开心-完整版.exe"
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
        spec = self.repo_root / "魔兽字体好开心-完整版.spec"
        if spec.exists():
            spec.unlink()
    
    def run(self):
        print("\n" + "=" * 50)
        print("  WoWFontsHappy - Full Version Build")
        print("  (Includes Node.js runtime)")
        print("=" * 50 + "\n")
        
        try:
            node_dir = self.download_node()
            app_dir = self.prepare_app()
            launcher_path = self.create_launcher(app_dir, node_dir)
            self.build(launcher_path, app_dir, node_dir)
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
