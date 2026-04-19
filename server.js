const express = require('express');
const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const os = require('os');
const fontkit = require('fontkit');

const app = express();
const PORT = 3456;

app.use(express.json({ charset: 'utf-8' }));

// 支持通过环境变量指定 public 目录，否则使用默认的 __dirname/public
const publicDir = process.env.PUBLIC_DIR || path.join(__dirname, 'public');

// 根路径返回 index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(publicDir, 'index.html'));
});

// 静态文件服务（禁用默认 index）
app.use(express.static(publicDir, { index: false }));

const SYSTEM_FONT_DIR = 'C:\\Windows\\Fonts';
const USER_FONT_DIR = path.join(os.homedir(), 'AppData', 'Local', 'Microsoft', 'Windows', 'Fonts');

const WOW_FONT_MAP = {
    zhCN: [
        { name: 'FRIZQT__.TTF', desc: '主界面字体（动作条、NPC名称、玩家名称、法术名称、物品名称、BUFF、按钮文本）' },
        { name: 'ARIALN.TTF', desc: '数字字体（生命条/经验条数字、头顶血条数字）' },
        { name: 'ARHei.TTF', desc: '说明字体（物品/技能说明文本、聊天框字体）' },
        { name: 'ARKai_C.TTF', desc: '战斗数字（坐标、生命值、法力值、战斗伤害数字）' },
        { name: 'ARKai_T.TTF', desc: '聊天字体（聊天、任务说明、书信正文、登录画面、标题）' }
    ],
    enUS: [
        { name: 'FRIZQT__.TTF', desc: '主UI字体（NPC名称、玩家名称、法术名称、BUFF、按钮文本）' },
        { name: 'ARIALN.TTF', desc: '聊天字体、信息文本、小号文本' },
        { name: 'skurri.ttf', desc: '战斗数字（浮动战斗数字）' },
        { name: 'MORPHEUS.ttf', desc: '书信字体（邮件、任务日志标题、书本）' },
        { name: 'DAMAGE.ttf', desc: '伤害字体' },
        { name: 'FRIENDS.ttf', desc: '好友列表文本' }
    ],
    zhTW: [
        { name: 'FRIZQT__.TTF', desc: '主界面字体' },
        { name: 'ARIALN.TTF', desc: '数字字体' },
        { name: 'bHEI00M.TTF', desc: '说明字体（物品/技能说明）' },
        { name: 'bHEI01B.TTF', desc: '聊天字体（聊天、任务说明、书信）' },
        { name: 'bKAI00M.TTF', desc: '战斗数字' },
        { name: 'bLEI00D.TTF', desc: '主界面文本' },
        { name: 'arheiuhk_bd.TTF', desc: '替代字体' }
    ],
    koKR: [
        { name: 'FRIZQT__.TTF', desc: '主界面字体' },
        { name: 'ARIALN.TTF', desc: '数字字体' },
        { name: '2002.ttf', desc: '战斗数字' },
        { name: '2002B.ttf', desc: '书信字体' },
        { name: 'K_Damage.ttf', desc: '伤害字体' },
        { name: 'K_Pagetext.ttf', desc: '页面文本' }
    ]
};

const WOW_VERSION_DIRS = [
    { key: '_retail_', label: '正式服 (Retail)' },
    { key: '_classic_', label: '怀旧服 (Cata/MoP)' },
    { key: '_classic_era_', label: '探索赛季/硬核 (Classic Era)' },
    { key: '_classic_titan_', label: '时光泰坦服' },
    { key: '_anniversary_', label: '20周年纪念服' }
];

// 使用 fontkit 读取字体文件的本地化名称
function getFontFamilyNameFromFile(fontPath) {
    try {
        const fonts = fontkit.openSync(fontPath);
        // TTC 文件包含多个字体，取第一个
        const font = fonts.fonts ? fonts.fonts[0] : fonts;
        
        if (!font.name || !font.name.records) return null;
        
        const records = font.name.records;
        
        // 优先获取中文字体名称 - 尝试所有可能的 key
        if (records.fontFamily) {
            const ff = records.fontFamily;
            // 尝试简体中文
            if (ff.zh) return ff.zh;
            if (ff['zh-CN']) return ff['zh-CN'];
            // 尝试繁体中文
            if (ff['zh-Hant']) return ff['zh-Hant'];
            if (ff['zh-TW']) return ff['zh-TW'];
            if (ff['zh-HK']) return ff['zh-HK'];
            // 尝试其他中文变体
            if (ff['zh-MO']) return ff['zh-MO'];
            if (ff['zh-SG']) return ff['zh-SG'];
            // 尝试日语（有些中文字体可能用日语编码）
            if (ff.ja) return ff.ja;
            if (ff.jp) return ff.jp;
            // 尝试韩语
            if (ff.ko) return ff.ko;
            // 回退到英文
            if (ff.en) return ff.en;
            // 如果没有 en，使用第一个可用的
            const keys = Object.keys(ff);
            if (keys.length > 0) return ff[keys[0]];
        }
        
        // 如果没有 fontFamily，尝试 fullName
        if (records.fullName) {
            const fn = records.fullName;
            if (fn.zh) return fn.zh;
            if (fn['zh-CN']) return fn['zh-CN'];
            if (fn['zh-Hant']) return fn['zh-Hant'];
            if (fn['zh-TW']) return fn['zh-TW'];
            if (fn['zh-HK']) return fn['zh-HK'];
            if (fn.ja) return fn.ja;
            if (fn.ko) return fn.ko;
            if (fn.en) return fn.en;
            const keys = Object.keys(fn);
            if (keys.length > 0) return fn[keys[0]];
        }
        
        return null;
    } catch (err) {
        console.error('读取字体名称失败:', fontPath, err.message);
        return null;
    }
}

// 从注册表读取字体名称（作为后备）
function readRegistryFontNames() {
    try {
        const output = execSync(
            `powershell -Command "$props = Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts'; $props.PSObject.Properties | Where-Object { $_.Name -notlike 'PS*' } | ForEach-Object { '{0}|{1}' -f $_.Name, $_.Value }"`,
            { encoding: 'utf8', timeout: 10000 }
        );
        const fontMap = {};
        const lines = output.split('\n');
        for (const line of lines) {
            const pipeIdx = line.indexOf('|');
            if (pipeIdx === -1) continue;
            const displayName = line.substring(0, pipeIdx).trim();
            const fontFile = line.substring(pipeIdx + 1).trim();
            if (!fontFile) continue;
            // 移除 (TrueType) 等后缀
            const cleanName = displayName.replace(/\s*\(TrueType\)\s*|\s*\(OpenType\)\s*/gi, '').trim();
            if (!fontFile.includes(':\\')) {
                fontMap[fontFile.toLowerCase()] = cleanName;
            } else {
                const basename = path.basename(fontFile).toLowerCase();
                fontMap[basename] = cleanName;
            }
        }
        return fontMap;
    } catch {
        return {};
    }
}

function safePath(p) {
    return Buffer.from(p, 'utf-8').toString('utf-8');
}

// 查找字体文件（同时搜索系统目录和用户目录）
function findFontFile(filename) {
    // 首先尝试系统字体目录
    let filePath = path.join(SYSTEM_FONT_DIR, filename);
    if (fs.existsSync(filePath)) {
        return filePath;
    }
    
    // 然后尝试用户字体目录
    filePath = path.join(USER_FONT_DIR, filename);
    if (fs.existsSync(filePath)) {
        return filePath;
    }
    
    return null;
}

// 打开浏览器
function openBrowser(url) {
    const platform = os.platform();
    let command;
    
    if (platform === 'win32') {
        command = `start "" "${url}"`;
    } else if (platform === 'darwin') {
        command = `open "${url}"`;
    } else {
        command = `xdg-open "${url}"`;
    }
    
    try {
        execSync(command, { stdio: 'ignore' });
    } catch (e) {
        console.log('自动打开浏览器失败，请手动访问:', url);
    }
}

// 扫描字体目录的辅助函数
function scanFontDirectory(fontDir, registryNames) {
    const fonts = [];
    const fontExtensions = ['.ttf', '.otf', '.ttc'];
    
    if (!fs.existsSync(fontDir)) {
        return fonts;
    }
    
    const files = fs.readdirSync(fontDir);
    
    for (const file of files) {
        const ext = path.extname(file).toLowerCase();
        if (fontExtensions.includes(ext)) {
            const filePath = path.join(fontDir, file);
            let stat;
            try {
                stat = fs.statSync(filePath);
            } catch {
                continue;
            }
            
            // 优先使用 fontkit 从字体文件内部读取 Family Name
            let displayName = getFontFamilyNameFromFile(filePath);
            
            // 如果读取失败，使用注册表名称或文件名
            if (!displayName) {
                displayName = registryNames[file.toLowerCase()] || path.basename(file, ext);
            }
            
            fonts.push({
                filename: file,
                displayName: displayName,
                size: stat.size,
                extension: ext
            });
        }
    }
    
    return fonts;
}

app.get('/api/system-fonts', (req, res) => {
    try {
        const registryNames = readRegistryFontNames();
        
        // 扫描系统字体目录
        let fonts = scanFontDirectory(SYSTEM_FONT_DIR, registryNames);
        
        // 扫描用户字体目录
        const userFonts = scanFontDirectory(USER_FONT_DIR, registryNames);
        fonts = fonts.concat(userFonts);

        fonts.sort((a, b) => a.displayName.localeCompare(b.displayName, 'zh-CN'));
        res.json({ success: true, fonts, total: fonts.length });
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

app.get('/api/preview-font/:filename', (req, res) => {
    // 首先尝试从系统字体目录查找
    let filePath = path.join(SYSTEM_FONT_DIR, req.params.filename);
    if (fs.existsSync(filePath)) {
        return res.sendFile(filePath);
    }
    
    // 如果系统目录没有，尝试从用户字体目录查找
    filePath = path.join(USER_FONT_DIR, req.params.filename);
    if (fs.existsSync(filePath)) {
        return res.sendFile(filePath);
    }
    
    res.status(404).json({ error: 'Font not found' });
});

app.get('/api/wow-versions', (req, res) => {
    res.json({ success: true, versions: WOW_VERSION_DIRS, fontMap: WOW_FONT_MAP });
});

app.post('/api/detect-wow', (req, res) => {
    const { searchPaths } = req.body;
    const found = [];

    const commonPaths = searchPaths || [
        'C:\\Program Files (x86)\\World of Warcraft',
        'C:\\Program Files\\World of Warcraft',
        'D:\\World of Warcraft',
        'E:\\World of Warcraft',
        'D:\\Games\\World of Warcraft',
        'E:\\Games\\World of Warcraft'
    ];

    for (const basePath of commonPaths) {
        if (fs.existsSync(basePath)) {
            const versions = [];
            for (const ver of WOW_VERSION_DIRS) {
                const verPath = path.join(basePath, ver.key);
                if (fs.existsSync(verPath)) {
                    const fontsPath = path.join(verPath, 'Fonts');
                    versions.push({
                        ...ver,
                        path: verPath,
                        fontsPath,
                        fontsDirExists: fs.existsSync(fontsPath)
                    });
                }
            }
            if (versions.length > 0) {
                found.push({ basePath, versions });
            }
        }
    }

    res.json({ success: true, installations: found });
});

app.post('/api/copy-fonts', (req, res) => {
    const { sourceFonts, wowFontsPath, locale, customMappings } = req.body;

    if (!sourceFonts || !wowFontsPath || !locale) {
        return res.json({ success: false, error: '缺少必要参数' });
    }

    const destPath = safePath(wowFontsPath);
    console.log('复制字体到目录:', destPath);

    try {
        if (!fs.existsSync(destPath)) {
            console.log('目录不存在，尝试创建:', destPath);
            try {
                fs.mkdirSync(destPath, { recursive: true });
                console.log('目录创建成功');
            } catch (mkdirErr) {
                console.error('创建目录失败:', mkdirErr.message);
                return res.json({ 
                    success: false, 
                    error: `创建字体目录失败: ${mkdirErr.message}。请确保以管理员身份运行本工具，或手动在WoW目录中创建Fonts文件夹。` 
                });
            }
        }

        const mappings = customMappings || WOW_FONT_MAP[locale] || [];
        const results = [];

        for (const mapping of mappings) {
            const sourceFont = sourceFonts.find(f => f.targetName === mapping.name);
            if (!sourceFont) continue;

            const srcPath = findFontFile(sourceFont.filename);
            const dstPath = path.join(destPath, mapping.name);

            if (!srcPath) {
                results.push({ target: mapping.name, success: false, error: '源字体文件不存在' });
                continue;
            }

            try {
                const srcBuf = fs.readFileSync(srcPath);
                fs.writeFileSync(dstPath, srcBuf);
                results.push({ target: mapping.name, success: true });
            } catch (err) {
                results.push({ target: mapping.name, success: false, error: err.message });
            }
        }

        res.json({ success: true, results });
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

app.post('/api/batch-copy', (req, res) => {
    const { sourceFont, wowFontsPath, locale } = req.body;

    if (!sourceFont || !wowFontsPath || !locale) {
        return res.json({ success: false, error: '缺少必要参数' });
    }

    const destPath = safePath(wowFontsPath);
    console.log('批量复制字体到目录:', destPath);

    try {
        if (!fs.existsSync(destPath)) {
            console.log('目录不存在，尝试创建:', destPath);
            try {
                fs.mkdirSync(destPath, { recursive: true });
                console.log('目录创建成功');
            } catch (mkdirErr) {
                console.error('创建目录失败:', mkdirErr.message);
                return res.json({ 
                    success: false, 
                    error: `创建字体目录失败: ${mkdirErr.message}。请确保以管理员身份运行本工具，或手动在WoW目录中创建Fonts文件夹。` 
                });
            }
        }

        const srcPath = findFontFile(sourceFont);
        if (!srcPath) {
            return res.json({ success: false, error: '源字体文件不存在' });
        }

        const srcBuf = fs.readFileSync(srcPath);
        const mappings = WOW_FONT_MAP[locale] || [];
        const results = [];

        for (const mapping of mappings) {
            const dstPath = path.join(destPath, mapping.name);
            try {
                fs.writeFileSync(dstPath, srcBuf);
                results.push({ target: mapping.name, success: true });
            } catch (err) {
                results.push({ target: mapping.name, success: false, error: err.message });
            }
        }

        res.json({ success: true, results });
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

app.post('/api/clear-fonts', (req, res) => {
    const { wowFontsPath } = req.body;
    if (!wowFontsPath) {
        return res.json({ success: false, error: '缺少路径参数' });
    }

    const destPath = safePath(wowFontsPath);

    try {
        if (!fs.existsSync(destPath)) {
            return res.json({ success: true, message: '字体目录不存在，无需清理' });
        }

        const files = fs.readdirSync(destPath);
        let deleted = 0;
        for (const file of files) {
            const ext = path.extname(file).toLowerCase();
            if (['.ttf', '.otf', '.ttc', '.slug'].includes(ext)) {
                fs.unlinkSync(path.join(destPath, file));
                deleted++;
            }
        }

        res.json({ success: true, deleted, message: `已删除 ${deleted} 个字体文件，游戏将使用默认字体` });
    } catch (err) {
        res.json({ success: false, error: err.message });
    }
});

// 启动服务器
const server = app.listen(PORT, () => {
    const url = `http://localhost:${PORT}`;
    console.log('\n========================================');
    console.log('  魔兽字体好开心已启动！');
    console.log('========================================');
    console.log(`  服务地址: ${url}`);
    console.log(`  系统字体目录: ${SYSTEM_FONT_DIR}`);
    console.log('========================================\n');
    console.log('  正在自动打开浏览器...\n');
    
    // 延迟1秒后打开浏览器，确保服务器已完全启动
    setTimeout(() => {
        openBrowser(url);
    }, 1000);
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('\n正在关闭服务...');
    server.close(() => {
        console.log('服务已关闭');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n正在关闭服务...');
    server.close(() => {
        console.log('服务已关闭');
        process.exit(0);
    });
});
