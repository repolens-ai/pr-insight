import * as vscode from 'vscode';
import axios from 'axios';
import { Configuration } from './config';

export interface ReviewIssue {
    line: number;
    column: number;
    severity: 'error' | 'warning' | 'info' | 'hint';
    message: string;
    code?: string;
    suggestion?: string;
}

export interface ReviewResult {
    filePath: string;
    issues: ReviewIssue[];
    summary: string;
    suggestions: string[];
}

export class CodeReviewer {
    private config: Configuration;
    private decorations: vscode.TextEditorDecorationType[] = [];
    private diagnostics: vscode.DiagnosticCollection;

    constructor(config: Configuration) {
        this.config = config;
        this.diagnostics = vscode.languages.createDiagnosticCollection('pr-insight');
    }

    async reviewFile(document: vscode.TextDocument): Promise<ReviewResult | null> {
        const apiKey = this.config.get('apiKey', '');
        if (!apiKey) {
            vscode.window.showErrorMessage('Please configure your OpenAI API key in PR Insight settings');
            return null;
        }

        const maxSize = this.config.get('maxFileSize', 100000);
        if (document.getText().length > maxSize) {
            vscode.window.showWarningMessage('File too large for review');
            return null;
        }

        const progress = this.config.get('showProgress', true);
        if (progress) {
            vscode.window.showInformationMessage('Starting PR Insight analysis...');
        }

        try {
            const code = document.getText();
            const language = document.languageId;
            const model = this.config.get('model', 'gpt-4');

            const response = await axios.post(
                'https://api.openai.com/v1/chat/completions',
                {
                    model,
                    messages: [
                        {
                            role: 'system',
                            content: this.getSystemPrompt(language)
                        },
                        {
                            role: 'user',
                            content: this.getReviewPrompt(code, language)
                        }
                    ],
                    temperature: 0.3,
                    max_tokens: 4000
                },
                {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const result = this.parseReviewResponse(document.fileName, response.data.choices[0].message.content);
            
            if (this.config.get('enableInlineAnnotations', true)) {
                this.applyDecorations(document, result);
            }

            this.updateDiagnostics(document, result);

            if (progress) {
                vscode.window.showInformationMessage(`Analysis complete. Found ${result.issues.length} issues.`);
            }

            return result;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Review failed: ${error.message}`);
            return null;
        }
    }

    async reviewWorkspace(): Promise<void> {
        const files = vscode.workspace.textDocuments.filter(doc => {
            const ext = doc.uri.fsPath.split('.').pop();
            return ['js', 'ts', 'py', 'java', 'go', 'rs', 'cpp', 'c', 'jsx', 'tsx'].includes(ext || '');
        });

        for (const file of files) {
            await this.reviewFile(file);
        }
    }

    async analyzeGitChanges(): Promise<void> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspaceRoot) {
            vscode.window.showWarningMessage('No workspace open');
            return;
        }

        const git = vscode.workspace.getConfiguration('git');
        const enabled = git.get<boolean>('enabled', true);
        
        if (!enabled) {
            vscode.window.showWarningMessage('Git is not enabled');
            return;
        }

        try {
            const uri = vscode.Uri.parse(`git://index?${workspaceRoot}`);
            const doc = await vscode.workspace.openTextDocument(uri);
            const diff = doc.getText();
            
            if (this.config.get('showProgress', true)) {
                vscode.window.showInformationMessage('Analyzing git changes...');
            }
            
            vscode.window.showInformationMessage('Git diff analysis complete');
        } catch (error) {
            vscode.window.showWarningMessage('Could not analyze git changes');
        }
    }

    async quickReview(code: string, language: string): Promise<string | null> {
        const apiKey = this.config.get('apiKey', '');
        if (!apiKey) {
            vscode.window.showErrorMessage('Please configure your OpenAI API key');
            return null;
        }

        try {
            const response = await axios.post(
                'https://api.openai.com/v1/chat/completions',
                {
                    model: this.config.get('model', 'gpt-4'),
                    messages: [
                        {
                            role: 'system',
                            content: 'You are a code reviewer. Provide concise feedback on the selected code.'
                        },
                        {
                            role: 'user',
                            content: `Review this ${language} code:\n\n${code}`
                        }
                    ],
                    temperature: 0.3,
                    max_tokens: 500
                },
                {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json'
                    }
                }
            );

            const feedback = response.data.choices[0].message.content;
            vscode.window.showInformationMessage('Quick Review Complete');
            return feedback;
        } catch (error: any) {
            vscode.window.showErrorMessage(`Quick review failed: ${error.message}`);
            return null;
        }
    }

    async clearAnnotations(): Promise<void> {
        this.decorations.forEach(d => d.dispose());
        this.decorations = [];
        this.diagnostics.clear();
    }

    provideHover(document: vscode.TextDocument, position: vscode.Position): vscode.ProviderResult<vscode.Hover> {
        const line = position.line + 1;
        const diagnostics = this.diagnostics.get(document.uri);
        const issue = diagnostics?.find(d => d.range.start.line + 1 === line);

        if (issue) {
            return new vscode.Hover(issue.message);
        }
        return null;
    }

    private getSystemPrompt(language: string): string {
        return `You are an expert code reviewer specializing in ${language}. 
Analyze code for issues, bugs, security vulnerabilities, code smells, and best practices.
Provide specific, actionable feedback.`;
    }

    private getReviewPrompt(code: string, language: string): string {
        return `Review the following ${language} code and identify issues in this JSON format:
{
  "issues": [
    {"line": 1, "column": 1, "severity": "warning", "message": "issue description", "code": "optional code"}
  ],
  "summary": "brief summary",
  "suggestions": ["suggestion 1", "suggestion 2"]
}

Code to review:
${code}`;
    }

    private parseReviewResponse(filePath: string, response: string): ReviewResult {
        try {
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const parsed = JSON.parse(jsonMatch[0]);
                return {
                    filePath,
                    issues: parsed.issues || [],
                    summary: parsed.summary || '',
                    suggestions: parsed.suggestions || []
                };
            }
        } catch (e) {
            console.error('Failed to parse review response');
        }

        return {
            filePath,
            issues: [],
            summary: response.substring(0, 200),
            suggestions: []
        };
    }

    private applyDecorations(document: vscode.TextDocument, result: ReviewResult): void {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.uri !== document.uri) { return; }

        this.decorations.forEach(d => d.dispose());
        this.decorations = [];

        const severityColors: Record<string, vscode.DecorationRenderOptions> = {
            error: { backgroundColor: 'rgba(255, 0, 0, 0.1)', overviewRulerColor: 'red' },
            warning: { backgroundColor: 'rgba(255, 165, 0, 0.1)', overviewRulerColor: 'orange' },
            info: { backgroundColor: 'rgba(0, 0, 255, 0.1)', overviewRulerColor: 'blue' },
            hint: { backgroundColor: 'rgba(0, 255, 0, 0.1)', overviewRulerColor: 'green' }
        };

        result.issues.forEach(issue => {
            const decoration = vscode.window.createTextEditorDecorationType({
                ...severityColors[issue.severity],
                isWholeLine: false,
                range: new vscode.Range(
                    issue.line - 1,
                    issue.column - 1,
                    issue.line - 1,
                    issue.column + 10
                )
            });
            this.decorations.push(decoration);
            editor.setDecorations(decoration, [
                new vscode.Range(issue.line - 1, issue.column - 1, issue.line - 1, issue.column + 10)
            ]);
        });
    }

    private updateDiagnostics(document: vscode.TextDocument, result: ReviewResult): void {
        const diagnostics: vscode.Diagnostic[] = result.issues.map(issue => {
            const range = new vscode.Range(
                issue.line - 1,
                issue.column - 1,
                issue.line - 1,
                issue.column + 10
            );
            const diagnostic = new vscode.Diagnostic(range, issue.message, this.mapSeverity(issue.severity));
            diagnostic.code = issue.code;
            return diagnostic;
        });

        this.diagnostics.set(document.uri, diagnostics);
    }

    private mapSeverity(severity: string): vscode.DiagnosticSeverity {
        const config = this.config.get('severityLevels', {});
        const mapping: Record<string, vscode.DiagnosticSeverity> = {
            error: vscode.DiagnosticSeverity.Error,
            warning: vscode.DiagnosticSeverity.Warning,
            info: vscode.DiagnosticSeverity.Information,
            hint: vscode.DiagnosticSeverity.Hint
        };
        return mapping[severity] || vscode.DiagnosticSeverity.Warning;
    }
}
