import * as vscode from 'vscode';

class MyDocumentSymbolProvider implements vscode.DocumentSymbolProvider {
    public provideDocumentSymbols(
        document: vscode.TextDocument,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.SymbolInformation[] | vscode.DocumentSymbol[]> {
        const symbols: vscode.SymbolInformation[] = [];

        // Parse the document and extract symbols
        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const callbackMatch = line.text.match(/\bon\s+(async_complete|controller|init|listener|midi_in|note(_controller)?|(n)?rpn|release|persistence_changed|(_)?pgs_changed|poly_at|ui_(control(\s*\([\w.#]+\)|(s)?)|update))|on_(pgs_changed|post_init|release)/);
            const constBlockMatch = line.text.match(/^\s*const\s+([\w.]+)\b/);
            const functionMatch = line.text.match(/^\s*(function|taskfunc)\s+([\w.]+)\s*\(?/);
            const macroMatch = line.text.match(/^\s*macro\s+([\w#.]+)\s*\(?/);
            const familyMatch = line.text.match(/^\s*family\s+([\w.]+)\b/);
            const listMatch = line.text.match(/(?:declare\s+)?list\s+([$%~?@!]?[\w.]+)\s*(?:\[)/);
            const structMatch = line.text.match(/^\s*struct\s+([\w.]+)\b/);
            const sectionMatch = line.text.match(/^\s*{{\s+(.*)\s+}}\s*/);

            if (callbackMatch) {
                const name = callbackMatch[0];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Event,
                    "callback",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (constBlockMatch) {
                const name = constBlockMatch[1];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Enum,
                    "constant block",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (functionMatch) {
                const name = functionMatch[2];
                const containerName = functionMatch[1] as string;
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Function,
                    containerName,
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (macroMatch) {
                const name = macroMatch[1];
                const containerName = macroMatch[1] as string;
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Number,
                    "macro",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (familyMatch) {
                const name = familyMatch[1];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Namespace,
                    "family",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (listMatch) {
                const name = listMatch[1];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Array,
                    "list",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (structMatch) {
                const name = structMatch[1];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.Struct,
                    "struct",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }

            if (sectionMatch) {
                const name = sectionMatch[1];
                const symbol = new vscode.SymbolInformation(
                    name,
                    vscode.SymbolKind.String,
                    "section",
                    new vscode.Location(document.uri, line.range)
                );

                symbols.push(symbol);
            }
        }

        return symbols;
    }
}

export function activate(context: vscode.ExtensionContext) {
    const symbolProvider = new MyDocumentSymbolProvider();

    context.subscriptions.push(
        vscode.languages.registerDocumentSymbolProvider({ scheme: 'file', language: 'sksp' }, symbolProvider)
    );
}