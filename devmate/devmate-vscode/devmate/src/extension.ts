import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {

    let disposable = vscode.commands.registerCommand(
        'devmate.analyze',
        async () => {

            const editor = vscode.window.activeTextEditor;

            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const selection = editor.selection;
            const text = editor.document.getText(selection);

            if (!text) {
                vscode.window.showErrorMessage('No code selected');
                return;
            }

            vscode.window.showInformationMessage('Analyzing code...');

            try {

                const response = await axios.post(
                    'http://10.139.79.163:8000/analyze-code',
                    {
                        language: editor.document.languageId,
                        code: text
                    }
                );

                const panel = vscode.window.createWebviewPanel(
                    'devmate',
                    'DevMate Analysis',
                    vscode.ViewColumn.Beside,
                    {}
                );

                panel.webview.html = `
                    <html>
                    <body style="
                        font-family: sans-serif;
                        padding: 20px;
                    ">
                        <h2>DevMate Analysis</h2>
                        <pre style="
                            white-space: pre-wrap;
                            line-height: 1.5;
                        ">${response.data.analysis}</pre>
                    </body>
                    </html>
                `;

            } catch (err) {

                vscode.window.showErrorMessage(
                    'Failed to contact backend'
                );

            }

        }
    );

    context.subscriptions.push(disposable);
}

export function deactivate() {}