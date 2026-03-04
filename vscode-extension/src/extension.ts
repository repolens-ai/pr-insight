import * as vscode from 'vscode';
import { CodeReviewer } from './reviewer';
import { ReviewPanel } from './webview';
import { Configuration } from './config';

let reviewer: CodeReviewer | undefined;
let reviewPanel: ReviewPanel | undefined;

export function activate(context: vscode.ExtensionContext) {
    const config = new Configuration();
    reviewer = new CodeReviewer(config);

    context.subscriptions.push(
        vscode.commands.registerCommand('pr-insight.reviewFile', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No file open to review');
                return;
            }
            await reviewer?.reviewFile(editor.document);
        }),

        vscode.commands.registerCommand('pr-insight.reviewWorkspace', async () => {
            await reviewer?.reviewWorkspace();
        }),

        vscode.commands.registerCommand('pr-insight.analyzeChanges', async () => {
            await reviewer?.analyzeGitChanges();
        }),

        vscode.commands.registerCommand('pr-insight.runQuickReview', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) { return; }
            
            const selection = editor.selection;
            const selectedText = editor.document.getText(selection);
            if (!selectedText) {
                vscode.window.showWarningMessage('No text selected');
                return;
            }
            
            await reviewer?.quickReview(selectedText, editor.document.languageId);
        }),

        vscode.commands.registerCommand('pr-insight.clearAnnotations', async () => {
            await reviewer?.clearAnnotations();
        }),

        vscode.commands.registerCommand('pr-insight.showSettings', async () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'pr-insight');
        })
    );

    vscode.workspace.onDidSaveTextDocument(async (document: vscode.TextDocument) => {
        if (config.get('reviewOnSave', false)) {
            await reviewer?.reviewFile(document);
        }
    });

    if (config.get('enableHoverDetails', true)) {
        const hoverProvider = vscode.languages.registerHoverProvider('*', {
            provideHover: (document, position) => reviewer?.provideHover(document, position)
        });
        context.subscriptions.push(hoverProvider);
    }
}

export function deactivate() {}
