<div align="center">

<img src="https://img.shields.io/badge/WoWFontsHappy-Font%20Manager-5599FF?style=for-the-badge&logo=battle.net&logoColor=white" alt="WoWFontsHappy">

# 🎮 WoWFontsHappy

**WoWFontsHappy - 魔兽世界字体管理器，浏览系统字体，一键替换WoW字体**

[![License](https://img.shields.io/badge/License-MIT-7C61D6.svg)](LICENSE)
[![Node.js](https://img.shields.io/badge/Node.js-18+-89C245.svg)](https://nodejs.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-CC4D%20D.svg)](https://www.microsoft.com/windows)

[下载](#下载) • [功能](#功能特性) • [使用](#使用方法) • [截图](#界面预览) • [开发](#开发构建)

</div>

---

## 📖 简介

**WoWFontsHappy**（魔兽字体好开心）是一款专为《魔兽世界》玩家打造的字体管理工具。它可以帮助你：

- 🔍 **浏览系统字体** - 自动扫描并展示系统中所有已安装字体
- 🎨 **实时预览** - 即时查看字体效果，支持中英文预览
- ⚡ **一键替换** - 快速替换WoW各版本的字体文件
- 🌍 **多版本支持** - 支持正式服、怀旧服、探索赛季等多个版本
- 🌐 **多语系适配** - 支持简中、繁中、英文、韩文客户端

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🖥️ **系统字体浏览** | 自动扫描 Windows 系统字体目录，支持用户字体 |
| 🔎 **智能搜索** | 快速搜索字体名称，支持中英文 |
| 👁️ **实时预览** | 卡片式展示，即时预览字体效果 |
| 🎯 **多版本检测** | 自动检测 WoW 安装路径及各版本目录 |
| 📝 **字体映射** | 清晰展示每个字体文件的用途说明 |
| 📦 **批量替换** | 一键将选定字体应用到所有目标文件 |
| 🛡️ **安全备份** | 自动备份原字体，随时可恢复 |
| 🌙 **暗黑主题** | 精心设计的深色界面，护眼舒适 |

---

## 📥 下载

### 方式一：直接下载可执行文件

前往 [Releases](https://github.com/yourusername/WoWFontsHappy/releases) 页面下载：

| 版本 | 文件名 | 大小 | 说明 |
|------|--------|------|------|
| **完整版** | `WoWFontsHappy-Full.exe` | ~80-100MB | 包含 Node.js 运行库，无需安装任何依赖 |
| **精简版** | `WoWFontsHappy-Mini.exe` | ~10-20MB | 需要系统已安装 Node.js 18+ |

> 💡 **推荐**：普通用户下载完整版，双击即可运行；开发者或已安装 Node.js 的用户可选择精简版。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/yourusername/WoWFontsHappy.git

# 进入目录
cd WoWFontsHappy

# 安装依赖
npm install

# 启动服务
npm start
```

---

## 🚀 使用方法

### 快速开始

1. **双击运行** `WoWFontsHappy-Full.exe` 或 `WoWFontsHappy-Mini.exe`
2. **等待加载** - 程序会自动扫描系统字体
3. **选择字体** - 在右侧点击你喜欢的字体卡片
4. **配置路径** - 输入或自动检测 WoW 安装目录
5. **应用字体** - 点击"一键替换"按钮

### 详细步骤

```
┌─────────────────────────────────────────────────────────────┐
│  1. 配置WoW路径（左侧）                                      │
│     • 输入WoW安装目录（如：I:\World of Warcraft）           │
│     • 点击"检测路径"自动识别各版本                           │
│                                                             │
│  2. 选择目标版本                                             │
│     • 勾选要修改的版本（正式服/怀旧服/探索赛季等）           │
│                                                             │
│  3. 浏览系统字体（右侧）                                     │
│     • 使用搜索框快速查找字体                                 │
│     • 点击字体卡片选中（可多选）                             │
│                                                             │
│  4. 应用字体                                                 │
│     • 点击"一键替换"按钮 - 全局替换所有字体                  │
│     • 或在字体映射表中精细化设置每个字体文件                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖼️ 界面预览

<div align="center">

| 主界面 | 字体选择 |
|:------:|:--------:|
| 深色主题，双栏布局 | 卡片式字体展示 |

</div>

---

## 🛠️ 开发构建

### 环境要求

- [Node.js](https://nodejs.org/) 18.0 或更高版本
- [Python](https://www.python.org/) 3.11+（用于打包）
- Windows 操作系统

### 本地开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm start
```

### 构建可执行文件

#### 本地打包

```bash
# 打包两个版本
python .github/scripts/build_all.py

# 或单独打包
python .github/scripts/build_full.py   # 完整版
python .github/scripts/build_mini.py   # 精简版
```

构建完成后，会在 `dist/` 目录生成：
- `WoWFontsHappy-Full.exe` - 完整版
- `WoWFontsHappy-Mini.exe` - 精简版

#### GitHub Actions 自动打包

推送标签自动触发构建并创建 Release：

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 📁 支持的WoW版本

| 版本 | 目录 | 状态 |
|------|------|:----:|
| 正式服 (Retail) | `_retail_` | ✅ |
| 怀旧服 (Cata/MoP) | `_classic_` | ✅ |
| 探索赛季/硬核 | `_classic_era_` | ✅ |
| 时光泰坦服 | `_classic_titan_` | ✅ |
| 20周年纪念服 | `_anniversary_` | ✅ |

---

## 🌐 支持的语言客户端

| 语言 | 客户端 | 字体文件 |
|------|--------|----------|
| 简体中文 | zhCN | FRIZQT__.TTF, ARHei.TTF, ARKai_C.TTF, ARKai_T.TTF, ARIALN.TTF |
| 繁体中文 | zhTW | FRIZQT__.TTF, ARIALN.TTF, bHEI00M.TTF, bHEI01B.TTF, bKAI00M.TTF, bLEI00D.TTF |
| 英文 | enUS | FRIZQT__.TTF, ARIALN.TTF, skurri.ttf, MORPHEUS.ttf, DAMAGE.ttf, FRIENDS.ttf |
| 韩文 | koKR | FRIZQT__.TTF, ARIALN.TTF, 2002.ttf, 2002B.ttf, K_Damage.ttf, K_Pagetext.ttf |

---

## 📂 项目结构

```
WoWFontsHappy/
├── .github/
│   ├── scripts/
│   │   ├── build_full.py    # 完整版打包脚本
│   │   ├── build_mini.py    # 精简版打包脚本
│   │   └── build_all.py     # 一键打包两个版本
│   └── workflows/
│       └── build.yml        # GitHub Actions 自动打包配置
├── public/
│   └── index.html           # 前端界面
├── server.js                # Express 后端服务
├── package.json             # 项目配置
├── package-lock.json        # 依赖锁定
└── README.md                # 项目说明
```

---

## 🧰 技术栈

- **后端**: [Node.js](https://nodejs.org/) + [Express](https://expressjs.com/)
- **字体解析**: [fontkit](https://github.com/foliojs/fontkit)
- **打包工具**: [PyInstaller](https://www.pyinstaller.org/)（替代 pkg，支持原生模块）

---

## ⚠️ 注意事项

1. **管理员权限**: 创建 WoW 字体文件夹需要管理员权限，建议右键以管理员身份运行
2. **游戏关闭**: 修改字体前请确保 WoW 客户端已关闭
3. **字体版权**: 请确保使用的字体拥有合法授权
4. **端口占用**: 程序使用 3456 端口，如被占用会自动终止占用进程

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 📄 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

---

## 🙏 致谢

- 黑科力研究所出品
- [黑科研]胡里胡涂

---

<div align="center">

**Made with ❤️ for WoW Players**

[⭐ Star this repo](https://github.com/yourusername/WoWFontsHappy) if you find it helpful!

</div>
