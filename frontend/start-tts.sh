#!/bin/bash
# TTS server launcher - run from WSL
cd /mnt/d/HermesWorkspace/girlgame-skill/frontend
"/mnt/f/ComfyUI_V6.0/ComfyUI-WorkFisher-V2/Python3.12.6/python.exe" -u server_tts.py > /tmp/tts_server.log 2>&1
