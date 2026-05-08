use std::{
    collections::{HashMap, HashSet},
    env, fs,
    path::{Path, PathBuf},
    process::Command,
};

use base64::{engine::general_purpose, Engine as _};
use regex::Regex;
use serde::{Deserialize, Serialize};
use tauri::{Manager, WindowEvent};

const SYSTEM_FONT_DIR: &str = "C:\\Windows\\Fonts";

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct AppConfig {
    success: bool,
    desktop_mode: bool,
    initial_wow_path: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WowVersion {
    key: String,
    label: String,
    path: Option<String>,
    fonts_path: Option<String>,
    fonts_dir_exists: Option<bool>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WowMapping {
    name: String,
    desc: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct WowVersionsResponse {
    success: bool,
    versions: Vec<WowVersion>,
    font_map: HashMap<String, Vec<WowMapping>>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct FontEntry {
    filename: String,
    display_name: String,
    size: u64,
    extension: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct FontsResponse {
    success: bool,
    fonts: Vec<FontEntry>,
    total: usize,
    custom_dir: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct PreviewFontResponse {
    success: bool,
    data_url: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct Installation {
    base_path: String,
    source: String,
    versions: Vec<WowVersion>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct DetectWowResponse {
    success: bool,
    installations: Vec<Installation>,
    searched: Vec<String>,
    error: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
struct SourceFont {
    filename: String,
    target_name: String,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct CopyResult {
    target: String,
    success: bool,
    error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct CopyResponse {
    success: bool,
    results: Vec<CopyResult>,
    error: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct ClearFontsResponse {
    success: bool,
    deleted: usize,
    message: String,
    error: Option<String>,
}

#[derive(Debug, Clone)]
struct PathCandidate {
    path: String,
    source: String,
}

pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            shutdown_app,
            app_config,
            wow_versions,
            system_fonts,
            preview_font,
            detect_wow,
            copy_fonts,
            batch_copy,
            clear_fonts
        ])
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                window.app_handle().exit(0);
            }
        })
        .run(tauri::generate_context!())
        .expect("failed to run Tauri application");
}

#[tauri::command]
fn shutdown_app(app: tauri::AppHandle) {
    app.exit(0);
}

#[tauri::command]
fn app_config() -> AppConfig {
    AppConfig {
        success: true,
        desktop_mode: true,
        initial_wow_path: initial_wow_path(),
    }
}

#[tauri::command]
fn wow_versions() -> WowVersionsResponse {
    WowVersionsResponse {
        success: true,
        versions: wow_version_dirs(),
        font_map: wow_font_map(),
    }
}

#[tauri::command]
async fn system_fonts(custom_dir: Option<String>) -> FontsResponse {
    tauri::async_runtime::spawn_blocking(move || system_fonts_inner(custom_dir))
        .await
        .unwrap_or_else(|err| FontsResponse {
            success: false,
            fonts: Vec::new(),
            total: 0,
            custom_dir: None,
            error: Some(err.to_string()),
        })
}

fn system_fonts_inner(custom_dir: Option<String>) -> FontsResponse {
    match scan_fonts(custom_dir.clone()) {
        Ok(mut fonts) => {
            fonts.sort_by(|a, b| a.display_name.to_lowercase().cmp(&b.display_name.to_lowercase()));
            FontsResponse {
                success: true,
                total: fonts.len(),
                fonts,
                custom_dir: custom_dir.filter(|dir| !dir.trim().is_empty()),
                error: None,
            }
        }
        Err(err) => FontsResponse {
            success: false,
            fonts: Vec::new(),
            total: 0,
            custom_dir,
            error: Some(err),
        },
    }
}

#[tauri::command]
async fn preview_font(filename: String, custom_dir: Option<String>) -> PreviewFontResponse {
    tauri::async_runtime::spawn_blocking(move || preview_font_inner(filename, custom_dir))
        .await
        .unwrap_or_else(|err| PreviewFontResponse {
            success: false,
            data_url: None,
            error: Some(err.to_string()),
        })
}

fn preview_font_inner(filename: String, custom_dir: Option<String>) -> PreviewFontResponse {
    let Some(font_path) = find_font_file(&filename, custom_dir.as_deref()) else {
        return PreviewFontResponse {
            success: false,
            data_url: None,
            error: Some("Font not found".to_string()),
        };
    };

    match fs::read(&font_path) {
        Ok(bytes) => {
            let mime = match font_path
                .extension()
                .and_then(|ext| ext.to_str())
                .unwrap_or_default()
                .to_lowercase()
                .as_str()
            {
                "otf" => "font/otf",
                "ttc" => "font/collection",
                _ => "font/ttf",
            };
            PreviewFontResponse {
                success: true,
                data_url: Some(format!(
                    "data:{};base64,{}",
                    mime,
                    general_purpose::STANDARD.encode(bytes)
                )),
                error: None,
            }
        }
        Err(err) => PreviewFontResponse {
            success: false,
            data_url: None,
            error: Some(err.to_string()),
        },
    }
}

#[tauri::command]
async fn detect_wow(search_paths: Option<Vec<String>>) -> DetectWowResponse {
    tauri::async_runtime::spawn_blocking(move || detect_wow_inner(search_paths))
        .await
        .unwrap_or_else(|err| DetectWowResponse {
            success: false,
            installations: Vec::new(),
            searched: Vec::new(),
            error: Some(err.to_string()),
        })
}

fn detect_wow_inner(search_paths: Option<Vec<String>>) -> DetectWowResponse {
    let candidates = build_wow_search_paths(search_paths);
    let mut found = Vec::new();
    let mut seen_installations = HashSet::new();

    for candidate in &candidates {
        let base_path = PathBuf::from(&candidate.path);
        if !base_path.exists() {
            continue;
        }

        let mut versions = Vec::new();
        for version in wow_version_dirs() {
            let version_path = base_path.join(&version.key);
            if version_path.exists() {
                let fonts_path = version_path.join("Fonts");
                versions.push(WowVersion {
                    key: version.key,
                    label: version.label,
                    path: Some(path_to_string(&version_path)),
                    fonts_path: Some(path_to_string(&fonts_path)),
                    fonts_dir_exists: Some(fonts_path.exists()),
                });
            }
        }

        if !versions.is_empty() {
            let key = candidate.path.to_lowercase();
            if seen_installations.insert(key) {
                found.push(Installation {
                    base_path: candidate.path.clone(),
                    source: candidate.source.clone(),
                    versions,
                });
            }
        }
    }

    DetectWowResponse {
        success: true,
        installations: found,
        searched: candidates.into_iter().map(|candidate| candidate.path).collect(),
        error: None,
    }
}

#[tauri::command]
fn copy_fonts(
    source_fonts: Vec<SourceFont>,
    wow_fonts_path: String,
    locale: String,
    custom_dir: Option<String>,
) -> CopyResponse {
    if source_fonts.is_empty() || wow_fonts_path.trim().is_empty() || locale.trim().is_empty() {
        return CopyResponse {
            success: false,
            results: Vec::new(),
            error: Some("缺少必要参数".to_string()),
        };
    }

    let dest_path = PathBuf::from(&wow_fonts_path);
    if let Err(err) = fs::create_dir_all(&dest_path) {
        return CopyResponse {
            success: false,
            results: Vec::new(),
            error: Some(format!("创建字体目录失败: {err}")),
        };
    }

    let mappings = wow_font_map().remove(&locale).unwrap_or_default();
    let mut results = Vec::new();

    for mapping in mappings {
        let Some(source_font) = source_fonts
            .iter()
            .find(|source| source.target_name.eq_ignore_ascii_case(&mapping.name))
        else {
            continue;
        };

        let Some(src_path) = find_font_file(&source_font.filename, custom_dir.as_deref()) else {
            results.push(CopyResult {
                target: mapping.name,
                success: false,
                error: Some("源字体文件不存在".to_string()),
            });
            continue;
        };

        let dst_path = dest_path.join(&mapping.name);
        results.push(copy_one_font(&src_path, &dst_path, &mapping.name));
    }

    CopyResponse {
        success: true,
        results,
        error: None,
    }
}

#[tauri::command]
fn batch_copy(
    source_font: String,
    wow_fonts_path: String,
    locale: String,
    custom_dir: Option<String>,
) -> CopyResponse {
    if source_font.trim().is_empty() || wow_fonts_path.trim().is_empty() || locale.trim().is_empty()
    {
        return CopyResponse {
            success: false,
            results: Vec::new(),
            error: Some("缺少必要参数".to_string()),
        };
    }

    let dest_path = PathBuf::from(&wow_fonts_path);
    if let Err(err) = fs::create_dir_all(&dest_path) {
        return CopyResponse {
            success: false,
            results: Vec::new(),
            error: Some(format!("创建字体目录失败: {err}")),
        };
    }

    let Some(src_path) = find_font_file(&source_font, custom_dir.as_deref()) else {
        return CopyResponse {
            success: false,
            results: Vec::new(),
            error: Some("源字体文件不存在".to_string()),
        };
    };

    let mappings = wow_font_map().remove(&locale).unwrap_or_default();
    let results = mappings
        .iter()
        .map(|mapping| copy_one_font(&src_path, &dest_path.join(&mapping.name), &mapping.name))
        .collect();

    CopyResponse {
        success: true,
        results,
        error: None,
    }
}

#[tauri::command]
fn clear_fonts(wow_fonts_path: String) -> ClearFontsResponse {
    if wow_fonts_path.trim().is_empty() {
        return ClearFontsResponse {
            success: false,
            deleted: 0,
            message: String::new(),
            error: Some("缺少路径参数".to_string()),
        };
    }

    let dest_path = PathBuf::from(&wow_fonts_path);
    if !dest_path.exists() {
        return ClearFontsResponse {
            success: true,
            deleted: 0,
            message: "字体目录不存在，无需清理".to_string(),
            error: None,
        };
    }

    let mut deleted = 0;
    let entries = match fs::read_dir(&dest_path) {
        Ok(entries) => entries,
        Err(err) => {
            return ClearFontsResponse {
                success: false,
                deleted: 0,
                message: String::new(),
                error: Some(err.to_string()),
            };
        }
    };

    for entry in entries.flatten() {
        let path = entry.path();
        let should_delete = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| matches!(ext.to_lowercase().as_str(), "ttf" | "otf" | "ttc" | "slug"))
            .unwrap_or(false);

        if should_delete && fs::remove_file(path).is_ok() {
            deleted += 1;
        }
    }

    ClearFontsResponse {
        success: true,
        deleted,
        message: format!("已删除 {deleted} 个字体文件，游戏将使用默认字体"),
        error: None,
    }
}

fn copy_one_font(src_path: &Path, dst_path: &Path, target: &str) -> CopyResult {
    match fs::copy(src_path, dst_path) {
        Ok(_) => CopyResult {
            target: target.to_string(),
            success: true,
            error: None,
        },
        Err(err) => CopyResult {
            target: target.to_string(),
            success: false,
            error: Some(err.to_string()),
        },
    }
}

fn scan_fonts(custom_dir: Option<String>) -> Result<Vec<FontEntry>, String> {
    let registry_names = read_registry_font_names();
    let mut fonts = Vec::new();

    if let Some(custom_dir) = custom_dir.filter(|dir| !dir.trim().is_empty()) {
        if Path::new(&custom_dir).exists() {
            fonts.extend(scan_font_directory(Path::new(&custom_dir), &registry_names));
        }
    } else {
        fonts.extend(scan_font_directory(Path::new(SYSTEM_FONT_DIR), &registry_names));
        let user_dir = user_font_dir();
        fonts.extend(scan_font_directory(&user_dir, &registry_names));
    }

    Ok(fonts)
}

fn scan_font_directory(font_dir: &Path, registry_names: &HashMap<String, String>) -> Vec<FontEntry> {
    let mut fonts = Vec::new();
    let Ok(entries) = fs::read_dir(font_dir) else {
        return fonts;
    };

    for entry in entries.flatten() {
        let file_path = entry.path();
        let Some(ext) = file_path.extension().and_then(|ext| ext.to_str()) else {
            continue;
        };
        let ext = ext.to_lowercase();
        if !matches!(ext.as_str(), "ttf" | "otf" | "ttc") {
            continue;
        }

        let Ok(metadata) = entry.metadata() else {
            continue;
        };
        let Some(filename) = file_path
            .file_name()
            .and_then(|name| name.to_str())
            .map(str::to_string)
        else {
            continue;
        };

        let display_name = registry_names
            .get(&filename.to_lowercase())
            .cloned()
            .unwrap_or_else(|| {
                file_path
                    .file_stem()
                    .and_then(|name| name.to_str())
                    .unwrap_or(&filename)
                    .to_string()
            });

        fonts.push(FontEntry {
            filename,
            display_name,
            size: metadata.len(),
            extension: format!(".{ext}"),
        });
    }

    fonts
}

fn read_registry_font_names() -> HashMap<String, String> {
    let mut font_map = HashMap::new();
    for key in [
        "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts",
        "HKCU\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts",
    ] {
        let Ok(output) = Command::new("reg").args(["query", key]).output() else {
            continue;
        };
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            let Some((display_name, value)) = parse_reg_value_line(line) else {
                continue;
            };
            let clean_name = display_name
                .replace("(TrueType)", "")
                .replace("(OpenType)", "")
                .trim()
                .to_string();
            if clean_name.is_empty() || value.is_empty() {
                continue;
            }
            let file_name = Path::new(&value)
                .file_name()
                .and_then(|name| name.to_str())
                .unwrap_or(&value)
                .to_lowercase();
            font_map.insert(file_name, clean_name);
        }
    }
    font_map
}

fn parse_reg_value_line(line: &str) -> Option<(String, String)> {
    let trimmed = line.trim();
    let type_pos = trimmed.find("REG_")?;
    let name = trimmed[..type_pos].trim();
    let rest = &trimmed[type_pos..];
    let mut parts = rest.splitn(2, char::is_whitespace);
    let _type_name = parts.next()?;
    let value = parts.next()?.trim();
    Some((name.to_string(), value.to_string()))
}

fn find_font_file(filename: &str, custom_dir: Option<&str>) -> Option<PathBuf> {
    if let Some(custom_dir) = custom_dir.filter(|dir| !dir.trim().is_empty()) {
        let file_path = Path::new(custom_dir).join(filename);
        if file_path.exists() {
            return Some(file_path);
        }
    }

    let system_path = Path::new(SYSTEM_FONT_DIR).join(filename);
    if system_path.exists() {
        return Some(system_path);
    }

    let user_path = user_font_dir().join(filename);
    if user_path.exists() {
        return Some(user_path);
    }

    None
}

fn build_wow_search_paths(search_paths: Option<Vec<String>>) -> Vec<PathCandidate> {
    if let Some(search_paths) = search_paths.filter(|paths| !paths.is_empty()) {
        let mut candidates = Vec::new();
        let mut seen = HashSet::new();
        for search_path in search_paths {
            add_path_candidate(&mut candidates, &mut seen, &search_path, "手动输入");
        }
        return candidates;
    }

    let mut candidates = Vec::new();
    let mut seen = HashSet::new();

    add_path_candidate(&mut candidates, &mut seen, &initial_wow_path(), "启动参数");
    if let Ok(path) = env::var("WOW_GAME_PATH") {
        add_path_candidate(&mut candidates, &mut seen, &path, "环境变量");
    }
    if let Ok(path) = env::var("WOW_PATH") {
        add_path_candidate(&mut candidates, &mut seen, &path, "环境变量");
    }

    for registry_path in read_registry_wow_paths() {
        add_path_candidate(&mut candidates, &mut seen, &registry_path, "注册表");
    }

    for battle_net_path in read_battle_net_wow_paths() {
        add_path_candidate(&mut candidates, &mut seen, &battle_net_path, "Battle.net");
    }

    for root in get_drive_roots() {
        for common_dir in [
            root.join("World of Warcraft"),
            root.join("Games").join("World of Warcraft"),
            root.join("Game").join("World of Warcraft"),
            root.join("Blizzard").join("World of Warcraft"),
            root.join("Battle.net").join("World of Warcraft"),
            root.join("Program Files").join("World of Warcraft"),
            root.join("Program Files (x86)").join("World of Warcraft"),
            root.join("暴雪游戏").join("World of Warcraft"),
            root.join("游戏").join("World of Warcraft"),
        ] {
            add_path_candidate(
                &mut candidates,
                &mut seen,
                &path_to_string(&common_dir),
                "常见目录",
            );
        }
    }

    candidates
}

fn add_path_candidate(
    candidates: &mut Vec<PathCandidate>,
    seen: &mut HashSet<String>,
    input_path: &str,
    source: &str,
) {
    let Some(normalized) = normalize_candidate_path(input_path) else {
        return;
    };
    let key = normalized.to_lowercase();
    if seen.insert(key) {
        candidates.push(PathCandidate {
            path: normalized,
            source: source.to_string(),
        });
    }
}

fn normalize_candidate_path(input_path: &str) -> Option<String> {
    let mut candidate = input_path
        .trim()
        .trim_matches('"')
        .trim_matches('\'')
        .replace('\0', "")
        .replace('/', "\\");
    if candidate.is_empty() {
        return None;
    }

    let mut path = PathBuf::from(&candidate);
    if path
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.eq_ignore_ascii_case("exe"))
        .unwrap_or(false)
    {
        path = path.parent()?.to_path_buf();
    }

    let basename = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or_default()
        .to_lowercase();

    if basename == "fonts" {
        let version_dir = path
            .parent()
            .and_then(|parent| parent.file_name())
            .and_then(|name| name.to_str())
            .unwrap_or_default()
            .to_lowercase();
        if wow_version_keys().contains(version_dir.as_str()) {
            path = path.parent()?.parent()?.to_path_buf();
        }
    } else if wow_version_keys().contains(basename.as_str()) {
        path = path.parent()?.to_path_buf();
    }

    candidate = path_to_string(&path);
    while candidate.ends_with('\\') || candidate.ends_with('/') {
        candidate.pop();
    }
    Some(candidate)
}

fn read_registry_wow_paths() -> Vec<String> {
    let mut paths = Vec::new();
    for key in [
        "HKLM\\SOFTWARE\\WOW6432Node\\Blizzard Entertainment\\World of Warcraft",
        "HKLM\\SOFTWARE\\Blizzard Entertainment\\World of Warcraft",
        "HKCU\\SOFTWARE\\Blizzard Entertainment\\World of Warcraft",
        "HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\World of Warcraft",
        "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\World of Warcraft",
    ] {
        let Ok(output) = Command::new("reg").args(["query", key, "/s"]).output() else {
            continue;
        };
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            let Some((name, value)) = parse_reg_value_line(line) else {
                continue;
            };
            if matches!(
                name.to_lowercase().as_str(),
                "installpath" | "installlocation" | "gamepath" | "path"
            ) {
                paths.push(value);
            }
        }
    }
    paths
}

fn read_battle_net_wow_paths() -> Vec<String> {
    let mut results = Vec::new();
    let files = [
        env::var_os("PROGRAMDATA")
            .map(PathBuf::from)
            .map(|path| path.join("Battle.net").join("Agent").join("product.db")),
        env::var_os("PROGRAMDATA")
            .map(PathBuf::from)
            .map(|path| path.join("Battle.net").join("Agent").join("agent.db")),
        env::var_os("APPDATA")
            .map(PathBuf::from)
            .map(|path| path.join("Battle.net").join("Battle.net.config")),
        env::var_os("LOCALAPPDATA")
            .map(PathBuf::from)
            .map(|path| path.join("Battle.net").join("Battle.net.config")),
    ];

    let Ok(wow_path_regex) =
        Regex::new(r#"[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n\0]+\\)*World of Warcraft(?:\\[^\\/:*?"<>|\r\n\0]+)*"#)
    else {
        return results;
    };

    for file in files.into_iter().flatten() {
        let Ok(metadata) = fs::metadata(&file) else {
            continue;
        };
        if metadata.len() > 20 * 1024 * 1024 {
            continue;
        }
        let Ok(buffer) = fs::read(&file) else {
            continue;
        };

        let mut variants = vec![String::from_utf8_lossy(&buffer).to_string()];
        let utf16: Vec<u16> = buffer
            .chunks_exact(2)
            .map(|chunk| u16::from_le_bytes([chunk[0], chunk[1]]))
            .collect();
        variants.push(String::from_utf16_lossy(&utf16));

        for text in variants {
            let normalized = text.replace("\\\\", "\\");
            for matched in wow_path_regex.find_iter(&normalized) {
                results.push(matched.as_str().to_string());
            }
        }
    }

    results
}

fn get_drive_roots() -> Vec<PathBuf> {
    (b'C'..=b'Z')
        .map(|drive| PathBuf::from(format!("{}:\\", drive as char)))
        .filter(|path| path.exists())
        .collect()
}

fn initial_wow_path() -> String {
    if let Ok(path) = env::var("WOW_GAME_PATH").or_else(|_| env::var("WOW_PATH")) {
        return path;
    }

    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        if arg == "--wow-path" || arg == "--game-path" {
            return args.next().unwrap_or_default();
        }
        if let Some(value) = arg.strip_prefix("--wow-path=") {
            return value.to_string();
        }
        if let Some(value) = arg.strip_prefix("--game-path=") {
            return value.to_string();
        }
    }

    String::new()
}

fn user_font_dir() -> PathBuf {
    env::var_os("LOCALAPPDATA")
        .map(PathBuf::from)
        .or_else(|| {
            env::var_os("USERPROFILE")
                .map(PathBuf::from)
                .map(|path| path.join("AppData").join("Local"))
        })
        .unwrap_or_else(|| PathBuf::from("C:\\Users\\Default\\AppData\\Local"))
        .join("Microsoft")
        .join("Windows")
        .join("Fonts")
}

fn path_to_string(path: &Path) -> String {
    path.to_string_lossy().to_string()
}

fn wow_version_keys() -> HashSet<&'static str> {
    [
        "_retail_",
        "_classic_",
        "_classic_era_",
        "_classic_titan_",
        "_anniversary_",
    ]
    .into_iter()
    .collect()
}

fn wow_version_dirs() -> Vec<WowVersion> {
    [
        ("_retail_", "正式服 (Retail)"),
        ("_classic_", "怀旧服 (Cata/MoP)"),
        ("_classic_era_", "探索赛季/硬核 (Classic Era)"),
        ("_classic_titan_", "时光泰坦服"),
        ("_anniversary_", "20周年纪念服"),
    ]
    .into_iter()
    .map(|(key, label)| WowVersion {
        key: key.to_string(),
        label: label.to_string(),
        path: None,
        fonts_path: None,
        fonts_dir_exists: None,
    })
    .collect()
}

fn wow_font_map() -> HashMap<String, Vec<WowMapping>> {
    let mut map = HashMap::new();
    map.insert(
        "zhCN".to_string(),
        vec![
            mapping("FRIZQT__.TTF", "主界面字体（动作条、NPC名称、玩家名称、法术名称、物品名称、BUFF、按钮文本）"),
            mapping("ARIALN.TTF", "数字字体（生命条/经验条数字、头顶血条数字）"),
            mapping("ARHei.TTF", "说明字体（物品/技能说明文本、聊天框字体）"),
            mapping("ARKai_C.TTF", "战斗数字（坐标、生命值、法力值、战斗伤害数字）"),
            mapping("ARKai_T.TTF", "聊天字体（聊天、任务说明、书信正文、登录画面、标题）"),
        ],
    );
    map.insert(
        "enUS".to_string(),
        vec![
            mapping("FRIZQT__.TTF", "主 UI 字体（NPC名称、玩家名称、法术名称、BUFF、按钮文本）"),
            mapping("ARIALN.TTF", "聊天字体、信息文本、小号文本"),
            mapping("skurri.ttf", "战斗数字（浮动战斗数字）"),
            mapping("MORPHEUS.ttf", "书信字体（邮件、任务日志标题、书本）"),
            mapping("DAMAGE.ttf", "伤害字体"),
            mapping("FRIENDS.ttf", "好友列表文本"),
        ],
    );
    map.insert(
        "zhTW".to_string(),
        vec![
            mapping("FRIZQT__.TTF", "主界面字体"),
            mapping("ARIALN.TTF", "数字字体"),
            mapping("bHEI00M.TTF", "说明字体（物品/技能说明）"),
            mapping("bHEI01B.TTF", "聊天字体（聊天、任务说明、书信）"),
            mapping("bKAI00M.TTF", "战斗数字"),
            mapping("bLEI00D.TTF", "主界面文本"),
            mapping("arheiuhk_bd.TTF", "替代字体"),
        ],
    );
    map.insert(
        "koKR".to_string(),
        vec![
            mapping("FRIZQT__.TTF", "主界面字体"),
            mapping("ARIALN.TTF", "数字字体"),
            mapping("2002.ttf", "战斗数字"),
            mapping("2002B.ttf", "书信字体"),
            mapping("K_Damage.ttf", "伤害字体"),
            mapping("K_Pagetext.ttf", "页面文本"),
        ],
    );
    map
}

fn mapping(name: &str, desc: &str) -> WowMapping {
    WowMapping {
        name: name.to_string(),
        desc: desc.to_string(),
    }
}
