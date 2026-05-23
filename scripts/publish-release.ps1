# 将 dist/ 下 Windows 安装包发布到 GitHub Releases
# 用法: .\scripts\publish-release.ps1 -Tag v1.0.0
param(
  [string]$Tag = "v1.0.0"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dist = Join-Path $root "dist"

$files = @(
  Get-ChildItem -Path $dist -Filter "AVG-MengGongChang-*-win-x64.exe" -ErrorAction SilentlyContinue
  Get-ChildItem -Path $dist -Filter "AVG-MengGongChang-*-win-portable.exe" -ErrorAction SilentlyContinue
  Get-ChildItem -Path $dist -Filter "AVG-MengGongChang-*-win-x64.exe.blockmap" -ErrorAction SilentlyContinue
) | Where-Object { $_ }

if (-not $files) {
  Write-Error "未找到 dist/AVG-MengGongChang-*.exe，请先运行 npm run build:win"
}

gh auth status
if ($LASTEXITCODE -ne 0) {
  Write-Host "请先执行: gh auth login"
  exit 1
}

$notes = @"
## AVG梦工厂 $Tag

- Windows 安装版 + 便携版
- 应用内显示名：**AVG梦工厂**
- 含 Web 客户端、流式叙事、存档、月下长安 TTS（需另启 Python TTS 服务）

详见 [docs/RELEASE.md](https://github.com/nanihaikeyidai/meilin-dream-game/blob/main/docs/RELEASE.md)
"@

$assetArgs = $files | ForEach-Object { $_.FullName }
gh release create $Tag @assetArgs --title "AVG梦工厂 $Tag" --notes $notes --repo nanihaikeyidai/meilin-dream-game
