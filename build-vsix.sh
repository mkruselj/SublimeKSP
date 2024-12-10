echo "[Build SublimeKSP for VS Code] Converting .sublime-snippets to VS Code snippets..."
npx snippetToVsCode -s "snippets" -o "vscode/snippets.json"
echo "[Build SublimeKSP for VS Code] Transpiling extension entry point from TypeScript to JavaScript..."
npm run compile
echo "[Build SublimeKSP for VS Code] Building extension..."
npm run package