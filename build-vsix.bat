echo "[Build SublimeKSP for VS Code] Converting .sublime-snippets to VS Code snippets..."
call npx snippetToVsCode -s "snippets" -o "vscode/snippets.json"
echo "[Build SublimeKSP for VS Code] Building VS Code extension..."
npm run package