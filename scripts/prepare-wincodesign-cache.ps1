# electron-builder 在 GHA Windows 上解压 winCodeSign 会因符号链接失败。
# 预下载 7z 并用 7-Zip 解压，再将 darwin dylib 补齐为实体文件。
$ErrorActionPreference = "Stop"

$version = "2.6.0"
$cacheRoot = Join-Path $env:LOCALAPPDATA "electron-builder\Cache\winCodeSign"
$extractDir = Join-Path $cacheRoot "winCodeSign-$version"
$archive = Join-Path $cacheRoot "winCodeSign-$version.7z"
$url = "https://github.com/electron-userland/electron-builder-binaries/releases/download/winCodeSign-$version/winCodeSign-$version.7z"

function Test-WinCodeSignReady([string]$dir) {
  Test-Path (Join-Path $dir "darwin\10.12\lib\libcrypto.1.0.0.dylib")
}

function Fix-DarwinLibs([string]$dir) {
  $libDir = Join-Path $dir "darwin\10.12\lib"
  if (-not (Test-Path $libDir)) { return }
  $pairs = @{
    "libcrypto.dylib" = "libcrypto.1.0.0.dylib"
    "libssl.dylib"    = "libssl.1.0.0.dylib"
  }
  foreach ($link in $pairs.Keys) {
    $dest = Join-Path $libDir $link
    $src = Join-Path $libDir $pairs[$link]
    if ((Test-Path $src) -and -not (Test-Path $dest)) {
      Copy-Item $src $dest
      Write-Host "Created $link from $($pairs[$link])"
    }
  }
}

New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null

if (-not (Test-WinCodeSignReady $extractDir)) {
  if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }

  Write-Host "Downloading winCodeSign $version..."
  Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing

  $sevenZip = @(
    "${env:ProgramFiles}\7-Zip\7z.exe",
    "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1

  if (-not $sevenZip) {
    throw "7-Zip not found. Install 7-Zip or run on a runner with 7z preinstalled."
  }

  Write-Host "Extracting to $extractDir"
  & $sevenZip x $archive "-o$extractDir" -y | Out-Null
}

if (-not (Test-WinCodeSignReady $extractDir)) {
  throw "winCodeSign cache incomplete after extract: $extractDir"
}

Fix-DarwinLibs $extractDir
Write-Host "winCodeSign cache ready at $extractDir"
