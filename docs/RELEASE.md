# AVG-Skill v1.0 发布与打包

## 版本说明

**v1.0.0** 包含：

- Web 客户端（`npm run dev`）
- Electron 桌面版（内嵌本地服务器，支持 API 配置、存档、流式叙事）
- 校园 / 月下长安模板与立绘资源
- 自动存档与继续游戏引导

## 本地打包

### 环境要求

- Node.js ≥ 18
- Windows 打 Windows 包；macOS 打 Mac 包（**无法在 Windows 上直接生成 .dmg**）

```bash
npm install

# 若 Electron 下载失败（ECONNRESET），可设国内镜像后重试：
# Windows PowerShell: $env:ELECTRON_MIRROR="https://npmmirror.com/mirrors/electron/"
# macOS/Linux: export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/

# 开发运行桌面版
npm start

# 仅解压目录（快速验证，输出 dist/win-unpacked 等）
npm run pack

# Windows 安装包 + 便携版（.exe）
npm run build:win

# macOS 磁盘镜像 + zip（须在 Mac 上执行）
npm run build:mac
```

产物目录：**`dist/`**

| 平台 | 典型产物 |
|------|----------|
| Windows | `AVG-Skill-1.0.0-win-x64.exe`（安装程序）、`AVG-Skill-1.0.0-win-portable.exe` |
| macOS | `AVG-Skill-1.0.0-mac-x64.dmg`、`AVG-Skill-1.0.0-mac-arm64.dmg` |

### 配置 API（桌面版）

1. 首次启动在界面内填写 **Base URL / API Key / 模型**
2. 或在用户数据目录放置 `.env`（Windows 示例）：
   ```
   %APPDATA%\avg-skill\.env
   ```
   内容参考项目根目录 `.env.example`

### 可选：应用图标

将图标放入 `build/` 目录后重新打包：

- Windows: `build/icon.ico`
- macOS: `build/icon.icns`

未提供时使用 Electron 默认图标。

## GitHub Actions 自动构建

推送 **`v*`** 标签（如 `v1.0.0`）时，`.github/workflows/release.yml` 会在 **Windows 与 macOS** runner 上分别打包，并上传产物为 Actions Artifacts。

```bash
git tag v1.0.0
git push origin v1.0.0
```

在 GitHub 仓库 **Actions** 页下载对应平台的安装包。

## 发布 Checklist

- [ ] `npm run test:preflight:layout` 通过
- [ ] `npm run pack` 本地可启动
- [ ] `npm run build:win` / `npm run build:mac` 成功
- [ ] 更新 `README.md` 下载说明
- [ ] 打 tag 并推送触发 CI
