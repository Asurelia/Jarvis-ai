import * as vscode from 'vscode';
import { JarvisClient } from './jarvisClient';
import { ChatProvider } from './chatProvider';
import { VoiceHandler } from './voiceHandler';
import { TerminalIntegration } from './terminalIntegration';
import { IntelliSenseProvider } from './intellisenseProvider';

let jarvisClient: JarvisClient;
let chatProvider: ChatProvider;
let voiceHandler: VoiceHandler;
let terminalIntegration: TerminalIntegration;
let intellisenseProvider: IntelliSenseProvider;

export function activate(context: vscode.ExtensionContext) {
    console.log('JARVIS AI Assistant is now active!');

    // Configuration
    const config = vscode.workspace.getConfiguration('jarvis');
    const apiUrl = config.get<string>('apiUrl', 'http://localhost:5006');

    // Initialize JARVIS client
    jarvisClient = new JarvisClient(apiUrl);

    // Initialize providers
    chatProvider = new ChatProvider(jarvisClient);
    voiceHandler = new VoiceHandler(jarvisClient);
    terminalIntegration = new TerminalIntegration(jarvisClient);
    intellisenseProvider = new IntelliSenseProvider(jarvisClient);

    // Register chat view
    const chatView = vscode.window.createTreeView('jarvisChat', {
        treeDataProvider: chatProvider,
        showCollapseAll: true
    });

    // Register commands
    const commands = [
        // Chat commands
        vscode.commands.registerCommand('jarvis.chat', async () => {
            const message = await vscode.window.showInputBox({
                prompt: 'What would you like to ask JARVIS?',
                placeHolder: 'Type your message here...'
            });

            if (message) {
                await chatProvider.sendMessage(message);
            }
        }),

        // Code analysis commands
        vscode.commands.registerCommand('jarvis.explain', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }

            const selection = editor.selection;
            const code = editor.document.getText(selection.isEmpty ? undefined : selection);
            
            if (!code.trim()) {
                vscode.window.showErrorMessage('No code to explain');
                return;
            }

            const response = await jarvisClient.explainCode(code, {
                language: editor.document.languageId,
                filename: editor.document.fileName
            });

            await chatProvider.addMessage('assistant', response);
        }),

        vscode.commands.registerCommand('jarvis.refactor', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.selection.isEmpty) {
                vscode.window.showErrorMessage('Please select code to refactor');
                return;
            }

            const code = editor.document.getText(editor.selection);
            const response = await jarvisClient.refactorCode(code, {
                language: editor.document.languageId,
                context: 'refactoring'
            });

            // Show diff and apply if accepted
            const edit = new vscode.WorkspaceEdit();
            edit.replace(editor.document.uri, editor.selection, response.refactoredCode);
            
            const applied = await vscode.workspace.applyEdit(edit);
            if (applied) {
                vscode.window.showInformationMessage('Code refactored successfully');
                await chatProvider.addMessage('assistant', `Refactored code:\\n${response.explanation}`);
            }
        }),

        vscode.commands.registerCommand('jarvis.generateTests', async (uri: vscode.Uri) => {
            const document = await vscode.workspace.openTextDocument(uri);
            const code = document.getText();

            const tests = await jarvisClient.generateTests(code, {
                language: document.languageId,
                framework: 'auto-detect'
            });

            // Create test file
            const testFileName = getTestFileName(uri.fsPath, document.languageId);
            const testUri = vscode.Uri.file(testFileName);
            
            const edit = new vscode.WorkspaceEdit();
            edit.createFile(testUri);
            edit.insert(testUri, new vscode.Position(0, 0), tests.code);
            
            await vscode.workspace.applyEdit(edit);
            vscode.window.showTextDocument(testUri);
            
            await chatProvider.addMessage('assistant', `Generated tests for ${uri.fsPath}`);
        }),

        vscode.commands.registerCommand('jarvis.optimizeCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.selection.isEmpty) {
                vscode.window.showErrorMessage('Please select code to optimize');
                return;
            }

            const code = editor.document.getText(editor.selection);
            const response = await jarvisClient.optimizeCode(code, {
                language: editor.document.languageId,
                target: 'performance'
            });

            // Show optimization suggestions
            const panel = vscode.window.createWebviewPanel(
                'jarvisOptimization',
                'JARVIS Code Optimization',
                vscode.ViewColumn.Beside,
                { enableScripts: true }
            );

            panel.webview.html = createOptimizationWebview(response);
        }),

        // Voice commands
        vscode.commands.registerCommand('jarvis.voiceCommand', async () => {
            await voiceHandler.startListening();
        }),

        vscode.commands.registerCommand('jarvis.startListening', async () => {
            await voiceHandler.startContinuousListening();
        }),

        vscode.commands.registerCommand('jarvis.stopListening', async () => {
            voiceHandler.stopListening();
        }),

        // Terminal integration
        vscode.commands.registerCommand('jarvis.openTerminal', async () => {
            await terminalIntegration.createJarvisTerminal();
        })
    ];

    // Register IntelliSense provider
    const selector: vscode.DocumentSelector = [
        { scheme: 'file', language: 'javascript' },
        { scheme: 'file', language: 'typescript' },
        { scheme: 'file', language: 'python' },
        { scheme: 'file', language: 'java' },
        { scheme: 'file', language: 'cpp' },
        { scheme: 'file', language: 'csharp' },
        { scheme: 'file', language: 'go' },
        { scheme: 'file', language: 'rust' }
    ];

    const completionProvider = vscode.languages.registerCompletionItemProvider(
        selector,
        intellisenseProvider,
        '.', ':', '->', '::'
    );

    // Register hover provider
    const hoverProvider = vscode.languages.registerHoverProvider(
        selector,
        intellisenseProvider
    );

    // Add to context subscriptions
    context.subscriptions.push(
        chatView,
        completionProvider,
        hoverProvider,
        ...commands
    );

    // Set context for views
    vscode.commands.executeCommand('setContext', 'jarvis.chatEnabled', true);

    // Show welcome message
    vscode.window.showInformationMessage(
        'JARVIS AI Assistant is ready! Press Ctrl+Shift+J to start chatting.',
        'Open Chat'
    ).then(selection => {
        if (selection === 'Open Chat') {
            vscode.commands.executeCommand('jarvis.chat');
        }
    });
}

export function deactivate() {
    if (jarvisClient) {
        jarvisClient.disconnect();
    }
    if (voiceHandler) {
        voiceHandler.stopListening();
    }
}

function getTestFileName(filePath: string, language: string): string {
    const path = require('path');
    const ext = path.extname(filePath);
    const basename = path.basename(filePath, ext);
    const dirname = path.dirname(filePath);

    const testExtensions: { [key: string]: string } = {
        'javascript': '.test.js',
        'typescript': '.test.ts',
        'python': '_test.py',
        'java': 'Test.java',
        'cpp': '_test.cpp',
        'csharp': '.Tests.cs'
    };

    const testExt = testExtensions[language] || '.test' + ext;
    
    if (language === 'java') {
        return path.join(dirname, basename + testExt);
    } else {
        return path.join(dirname, basename + testExt);
    }
}

function createOptimizationWebview(response: any): string {
    return `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>JARVIS Code Optimization</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; padding: 20px; }
            .suggestion { margin: 15px 0; padding: 15px; border-left: 4px solid #007ACC; background: #f8f9fa; }
            .code { background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; font-family: 'Courier New', monospace; }
            .improvement { color: #28a745; font-weight: bold; }
            .warning { color: #ffc107; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🚀 Code Optimization Suggestions</h1>
        <div class="suggestion">
            <h3 class="improvement">Performance Improvements:</h3>
            <p>${response.improvements || 'No specific improvements identified.'}</p>
        </div>
        <div class="suggestion">
            <h3>Optimized Code:</h3>
            <div class="code">${response.optimizedCode || 'No optimization available.'}</div>
        </div>
        <div class="suggestion">
            <h3>Explanation:</h3>
            <p>${response.explanation || 'No explanation provided.'}</p>
        </div>
    </body>
    </html>
    `;
}`;