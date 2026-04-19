#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions - 精简版打包脚本
不包含 Node.js 运行库
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    # 路径设置
    repo_root = Path(__file__).parent.parent.parent
    app_dir = repo_root
    output_dir = repo_root / "dist"
    build_dir = repo_root / "build"
    
    print("=" * 50)
    print("  魔兽字体好开心 - 精简版打包")
    print("  (需要系统安装 Node.js)")
    print("=" * 50)
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        
        # 创建 launcher
        launcher_code = f'''
import os
import sys
import subprocess
from pathlib import Path

# 获取应用路径
if hasattr(sys, '_MEIPASS'):
    app_dir = Path(sys._MEIPASS) / "app"
else:
    app_dir = Path(__file__).parent / "app"

server_js = app_dir / "server.js"
public_dir = app_dir / "public"
index_html = public_dir / "index.html"

if not index_html.exists():
    print("[错误] 找不到 index.html")
    sys.exit(1)

# 检查 Node.js
try:
    subprocess.run(["node", "--version"], capture_output=True, check=True)
except:
    print("[错误] 未找到 Node.js，请先安装 Node.js")
    print("       下载地址: https://nodejs.org/")
    sys.exit(1)

# 终止占用 3456 端口的进程
print("[检查] 检查端口 3456 占用情况...")
try:
    result = subprocess.run(
        ['netstat', '-ano', '|', 'findstr', ':3456'],
        capture_output=True, text=True, shell=True
    )
    if ':3456' in result.stdout:
        print("[警告] 发现占用 3456 端口的进程，正在终止...")
        for line in result.stdout.strip().splitlines():
            if ':3456' in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                        print(f"[OK] 已终止进程 PID: {{pid}}")
                    except:
                        pass
        import time
        time.sleep(1)
    else:
        print("[OK] 端口 3456 未被占用")
except Exception as e:
    print(f"[警告] 检查端口时出错: {{e}}")

print("=" * 50)
print("  魔兽字体好开心")
print("=" * 50)
print("  地址: http://localhost:3456")
print("  按 Ctrl+C 停止")
print("=" * 50)
print()

# 设置环境变量
env = os.environ.copy()
env["PUBLIC_DIR"] = str(public_dir)

# 启动服务器
process = subprocess.Popen(
    f'node "{{server_js}}"',
    cwd=app_dir,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='replace',
    shell=True
)

# 读取输出
try:
    for line in process.stdout:
        print(line, end='')
except KeyboardInterrupt:
    print("")
    print("正在停止服务器...")
except Exception as e:
    print(f"[错误] 读取输出时出错: {{e}}")

# 终止进程
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
        
        print("\n构建 EXE...")
        
        # 清理 build 目录
        if build_dir.exists():
            shutil.rmtree(build_dir)
        
        # PyInstaller 参数
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
        print("[OK] 精简版构建完成")
        
        # 显示文件大小
        exe_path = output_dir / "WoWFontsHappy-Mini.exe"
        if exe_path.exists():
            size = exe_path.stat().st_size / (1024 * 1024)
            print(f"   文件: {exe_path}")
            print(f"   大小: {size:.1f} MB")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
