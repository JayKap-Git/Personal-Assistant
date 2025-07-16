import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
	console.log('🔥🔥 Extension activated!');

	vscode.workspace.onDidChangeTextDocument(event => {
		// Get full text of the changed document
		const text = event.document.getText();

		// Define output path (Desktop file)
		const outputPath = path.join(process.env.HOME || '', 'Desktop', 'vscode_live_text.txt');

		// Write text to file
		fs.writeFileSync(outputPath, text);
	});
}

export function deactivate() {}