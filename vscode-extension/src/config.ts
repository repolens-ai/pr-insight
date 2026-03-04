import * as vscode from 'vscode';

export class Configuration {
    private config: vscode.WorkspaceConfiguration;

    constructor() {
        this.config = vscode.workspace.getConfiguration('pr-insight');
    }

    get<T>(key: string, defaultValue: T): T {
        return this.config.get<T>(key, defaultValue);
    }

    async set(key: string, value: any): Promise<void> {
        await this.config.update(key, value, vscode.ConfigurationTarget.Global);
    }

    getApiKey(): string {
        return this.get<string>('apiKey', '');
    }

    getModel(): string {
        return this.get<string>('model', 'gpt-4');
    }

    getLanguage(): string {
        return this.get<string>('language', 'en');
    }

    isInlineAnnotationsEnabled(): boolean {
        return this.get<boolean>('enableInlineAnnotations', true);
    }

    isHoverDetailsEnabled(): boolean {
        return this.get<boolean>('enableHoverDetails', true);
    }

    isReviewOnSaveEnabled(): boolean {
        return this.get<boolean>('reviewOnSave', false);
    }

    getExcludePatterns(): string[] {
        return this.get<string[]>('excludePatterns', [
            '**/node_modules/**',
            '**/dist/**',
            '**/build/**',
            '**/.git/**'
        ]);
    }

    getMaxFileSize(): number {
        return this.get<number>('maxFileSize', 100000);
    }

    getCustomRules(): string[] {
        return this.get<string[]>('customRules', []);
    }
}
