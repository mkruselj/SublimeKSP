"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = void 0;
const vscode = __importStar(require("vscode"));
class MyDocumentSymbolProvider {
    provideDocumentSymbols(document, token) {
        const symbols = [];
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
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Event, "callback", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (constBlockMatch) {
                const name = constBlockMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Enum, "constant block", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (functionMatch) {
                const name = functionMatch[2];
                const containerName = functionMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Function, containerName, new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (macroMatch) {
                const name = macroMatch[1];
                const containerName = macroMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Number, "macro", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (familyMatch) {
                const name = familyMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Namespace, "family", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (listMatch) {
                const name = listMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Array, "list", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (structMatch) {
                const name = structMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.Struct, "struct", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
            if (sectionMatch) {
                const name = sectionMatch[1];
                const symbol = new vscode.SymbolInformation(name, vscode.SymbolKind.String, "section", new vscode.Location(document.uri, line.range));
                symbols.push(symbol);
            }
        }
        return symbols;
    }
}
function activate(context) {
    const symbolProvider = new MyDocumentSymbolProvider();
    context.subscriptions.push(vscode.languages.registerDocumentSymbolProvider({ scheme: 'file', language: 'sksp' }, symbolProvider));
}
exports.activate = activate;
