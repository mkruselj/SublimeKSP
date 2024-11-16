isNpmPackageInstalled()
{
    npm list --depth 1 -g $1 > /dev/null 2>&1
}

for package in convert-snippets-to-vscode
do
    if ! isNpmPackageInstalled $package
    then
        echo "[Build SublimeKSP for VS Code] Installing required npm package convert-snippets-to-vscode..."
        echo

        npm install -g $package
    fi

    echo
    echo "[Build SublimeKSP for VS Code] Converting .sublime-snippets to VS Code snippets..."
    echo

    snippetToVsCode -s "snippets" -o "vscode/snippets.json"

    echo
    echo "[Build SublimeKSP for VS Code] Building VS Code extension..."

    npm run package
done
