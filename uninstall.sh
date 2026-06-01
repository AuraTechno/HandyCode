#!/bin/bash
echo "========================================"
echo "  HandyCode Uninstaller"
echo "========================================"

echo "[1/4] Uninstalling package..."
pip3 uninstall handycode -y 2>/dev/null || pip uninstall handycode -y

echo "[2/4] Removing scripts..."
rm -f "$HOME/.local/bin/hc" "$HOME/.local/bin/handycode"

echo "[3/4] Removing configuration..."
rm -rf "$HOME/.handycode"

echo "[4/4] Clearing pip cache..."
pip cache purge 2>/dev/null

echo ""
echo "✅ HandyCode полностью удалён"