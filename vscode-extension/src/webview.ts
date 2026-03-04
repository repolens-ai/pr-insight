import * as vscode from 'vscode';
import { ReviewResult } from './reviewer';

export class ReviewPanel {
    private panel: vscode.WebviewPanel | undefined;

    constructor() {}

    showReviewResults(results: ReviewResult[]): void {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.Two);
        } else {
            this.panel = vscode.window.createWebviewPanel(
                'pr-insight-results',
                'PR Insight Results',
                vscode.ViewColumn.Two,
                {
                    enableScripts: true,
                    retainContextWhenHidden: true
                }
            );

            this.panel.onDidDispose(() => {
                this.panel = undefined;
            });
        }

        const html = this.generateHtml(results);
        this.panel.webview.html = html;
    }

    private generateHtml(results: ReviewResult[]): string {
        const issuesCount = results.reduce((sum, r) => sum + r.issues.length, 0);
        
        return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PR Insight Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        h1 {
            color: #569cd6;
            font-size: 1.5em;
            border-bottom: 1px solid #3c3c3c;
            padding-bottom: 10px;
        }
        .summary {
            background: #2d2d2d;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .file-section {
            margin-bottom: 20px;
            background: #252526;
            border-radius: 5px;
            overflow: hidden;
        }
        .file-header {
            background: #333333;
            padding: 10px 15px;
            font-weight: bold;
            cursor: pointer;
        }
        .file-header:hover {
            background: #3c3c3c;
        }
        .issues {
            padding: 10px 15px;
        }
        .issue {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid;
            background: #2d2d2d;
        }
        .issue.error { border-color: #f14c4c; }
        .issue.warning { border-color: #cca700; }
        .issue.info { border-color: #3794ff; }
        .issue.hint { border-color: #4ec9b0; }
        .issue-line {
            color: #858585;
            font-size: 0.9em;
        }
        .issue-message {
            margin-top: 5px;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-right: 10px;
        }
        .badge.error { background: #f14c4c; }
        .badge.warning { background: #cca700; }
        .badge.info { background: #3794ff; }
        .badge.hint { background: #4ec9b0; }
        .suggestions {
            margin-top: 20px;
            padding: 15px;
            background: #2d4f2f;
            border-radius: 5px;
        }
        .suggestion {
            padding: 5px 0;
        }
    </style>
</head>
<body>
    <h1>🔍 PR Insight - Code Review Results</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Files Reviewed:</strong> ${results.length}</p>
        <p><strong>Total Issues Found:</strong> ${issuesCount}</p>
    </div>

    ${results.map(result => `
        <div class="file-section">
            <div class="file-header">📄 ${this.getFileName(result.filePath)}</div>
            <div class="issues">
                ${result.issues.length === 0 ? '<p>No issues found ✅</p>' : 
                  result.issues.map(issue => `
                    <div class="issue ${issue.severity}">
                        <span class="badge ${issue.severity}">${issue.severity.toUpperCase()}</span>
                        <span class="issue-line">Line ${issue.line}, Column ${issue.column}</span>
                        <div class="issue-message">${issue.message}</div>
                        ${issue.suggestion ? `<div class="suggestion"><strong>💡 Suggestion:</strong> ${issue.suggestion}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('')}

    ${results.some(r => r.suggestions.length > 0) ? `
        <div class="suggestions">
            <h2>💡 Suggestions</h2>
            ${results.flatMap(r => r.suggestions).map(s => `
                <div class="suggestion">• ${s}</div>
            `).join('')}
        </div>
    ` : ''}

    <script>
        // Add click handlers for file headers
        document.querySelectorAll('.file-header').forEach(header => {
            header.addEventListener('click', () => {
                const issues = header.nextElementSibling;
                issues.style.display = issues.style.display === 'none' ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>`;
    }

    private getFileName(filePath: string): string {
        return filePath.split(/[/\\]/).pop() || filePath;
    }

    dispose(): void {
        if (this.panel) {
            this.panel.dispose();
        }
    }
}
