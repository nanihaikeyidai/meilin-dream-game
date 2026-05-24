@echo off
REM 使用 ComfyUI 自带 Python 生成各剧本参考音（需 GPU + VoxCPM2 模型）
set PY=F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\Python3.12.6\python.exe
set VOXCPM2_PATH=F:\ComfyUI_V6.0\ComfyUI-WorkFisher-V2\ComfyUI\models\VoxCPM2

if not exist "%PY%" (
  echo [refs] Python not found: %PY%
  echo Edit scripts\generate_voice_refs.bat to set your path.
  exit /b 1
)

cd /d %~dp0..
"%PY%" scripts\generate_voice_refs.py %*
