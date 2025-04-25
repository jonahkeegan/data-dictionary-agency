// VSCode Extension for ClinerRules Logger
const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const net = require('net');

/**
 * @typedef {Object} LoggerConfig
 * @property {boolean} enabled - Whether the logger is enabled
 * @property {string} serverHost - The host of the logger server
 * @property {number} serverPort - The port of the logger server
 * @property {string} rulesDir - The directory containing .clinerules files
 */

/**
 * @type {LoggerConfig}
 */
let config = {
    enabled: true,
    serverHost: '127.0.0.1',
    serverPort: 5678,
    rulesDir: null
};

/**
 * Find the user's .clinerules directory
 */
function findRulesDir() {
    // Start with default location based on OS
    let homeDir = process.env.HOME || process.env.USERPROFILE;
    if (!homeDir) {
        return null;
    }

    // Check for OneDrive/Documents/Cline/Rules
    let rulesDir = path.join(homeDir, 'OneDrive', 'Documents', 'Cline', 'Rules');
    
    if (fs.existsSync(rulesDir)) {
        return rulesDir;
    }
    
    // Check for Documents/Cline/Rules as fallback
    rulesDir = path.join(homeDir, 'Documents', 'Cline', 'Rules');
    
    if (fs.existsSync(rulesDir)) {
        return rulesDir;
    }
    
    // Check workspace settings
    const workspaceConfig = vscode.workspace.getConfiguration('clinerules');
    const configuredDir = workspaceConfig.get('rulesDirectory');
    
    if (configuredDir && fs.existsSync(configuredDir)) {
        return configuredDir;
    }
    
    return null;
}

/**
 * Check if a file is a .clinerules file
 * @param {vscode.Uri} uri - The file URI to check
 * @returns {boolean} True if the file is a .clinerules file
 */
function isClinerRulesFile(uri) {
    if (!uri || !uri.fsPath) {
        return false;
    }

    // If rules directory is not set, try to find it
    if (!config.rulesDir) {
        config.rulesDir = findRulesDir();
    }

    // If still not set or file doesn't exist, we can't check
    if (!config.rulesDir) {
        // Fallback to simple name check
        return path.extname(uri.fsPath) === '.md' && 
               (uri.fsPath.indexOf('clinerules') >= 0 || uri.fsPath.indexOf('Cline/Rules') >= 0);
    }

    // Check if the file is in the rules directory
    return uri.fsPath.startsWith(config.rulesDir) && path.extname(uri.fsPath) === '.md';
}

/**
 * Extract rule name from file path
 * @param {string} filePath - The file path to extract rule name from
 * @returns {string} The rule name
 */
function getRuleName(filePath) {
    if (!filePath) {
        return null;
    }
    
    return path.basename(filePath, path.extname(filePath));
}

/**
 * Send request to logger server
 * @param {Object} request - The request object
 * @returns {Promise<Object>} The response object
 */
function sendRequest(request) {
    return new Promise((resolve, reject) => {
        const client = new net.Socket();
        let responseData = '';

        client.connect(config.serverPort, config.serverHost, () => {
            client.write(JSON.stringify(request) + '\n\n');
        });

        client.on('data', (data) => {
            responseData += data.toString();
            
            // Check for end of message marker
            if (responseData.endsWith('\n\n')) {
                try {
                    const response = JSON.parse(responseData.trim());
                    resolve(response);
                    client.end();
                } catch (error) {
                    reject(new Error('Invalid response format'));
                    client.end();
                }
            }
        });

        client.on('error', (error) => {
            reject(error);
        });

        client.on('close', () => {
            if (!responseData.endsWith('\n\n')) {
                reject(new Error('Connection closed before response completed'));
            }
        });

        // Set a timeout
        setTimeout(() => {
            client.end();
            reject(new Error('Request timed out'));
        }, 5000);
    });
}

/**
 * Log a file interaction
 * @param {string} ruleName - The rule name
 * @param {string} interactionType - The interaction type (e.g., 'read', 'write')
 * @param {Object} metadata - Additional metadata
 * @returns {Promise<Object>} The response object
 */
async function logInteraction(ruleName, interactionType, metadata = {}) {
    if (!config.enabled || !ruleName) {
        return { success: false, error: 'Logger disabled or invalid rule name' };
    }

    const request = {
        action: 'log_interaction',
        rule_name: ruleName,
        interaction_type: interactionType,
        application: 'vscode_extension',
        metadata: {
            ...metadata,
            vscode_version: vscode.version,
            timestamp: new Date().toISOString()
        }
    };

    try {
        return await sendRequest(request);
    } catch (error) {
        console.error('Failed to log interaction:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Log a rule execution
 * @param {string} ruleName - The rule name
 * @param {string} componentName - The component name (optional)
 * @param {string} taskDocument - The task document (optional)
 * @param {string} notes - Additional notes (optional)
 * @returns {Promise<Object>} The response object
 */
async function logRuleExecution(ruleName, componentName = null, taskDocument = null, notes = null) {
    if (!config.enabled || !ruleName) {
        return { success: false, error: 'Logger disabled or invalid rule name' };
    }

    const request = {
        action: 'log_rule_execution',
        rule_name: ruleName,
        component_name: componentName,
        task_document: taskDocument,
        notes: notes
    };

    try {
        return await sendRequest(request);
    } catch (error) {
        console.error('Failed to log rule execution:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Ping the logger server to check if it's running
 * @returns {Promise<boolean>} True if the server is running
 */
async function pingServer() {
    try {
        const response = await sendRequest({ action: 'ping' });
        return response && response.success && response.message === 'pong';
    } catch (error) {
        console.error('Failed to ping server:', error);
        return false;
    }
}

/**
 * Get recent interactions
 * @param {number} limit - Maximum number of interactions to return
 * @returns {Promise<Object[]>} Array of interactions
 */
async function getRecentInteractions(limit = 10) {
    try {
        const response = await sendRequest({
            action: 'get_recent_interactions',
            limit: limit
        });

        if (response && response.success && Array.isArray(response.interactions)) {
            return response.interactions;
        }
        return [];
    } catch (error) {
        console.error('Failed to get recent interactions:', error);
        return [];
    }
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('ClinerRules Logger extension activated');
    
    // Initialize configuration
    const workspaceConfig = vscode.workspace.getConfiguration('clinerules');
    config.enabled = workspaceConfig.get('enabled', true);
    config.serverHost = workspaceConfig.get('serverHost', '127.0.0.1');
    config.serverPort = workspaceConfig.get('serverPort', 5678);
    config.rulesDir = findRulesDir();

    // Register file event handlers
    const fileOpenListener = vscode.workspace.onDidOpenTextDocument(document => {
        if (isClinerRulesFile(document.uri)) {
            const ruleName = getRuleName(document.uri.fsPath);
            logInteraction(ruleName, 'opened', {
                lineCount: document.lineCount,
                languageId: document.languageId
            });
        }
    });

    const fileSaveListener = vscode.workspace.onDidSaveTextDocument(document => {
        if (isClinerRulesFile(document.uri)) {
            const ruleName = getRuleName(document.uri.fsPath);
            logInteraction(ruleName, 'saved', {
                lineCount: document.lineCount,
                languageId: document.languageId
            });
        }
    });

    const fileCloseListener = vscode.workspace.onDidCloseTextDocument(document => {
        if (isClinerRulesFile(document.uri)) {
            const ruleName = getRuleName(document.uri.fsPath);
            logInteraction(ruleName, 'closed', {
                lineCount: document.lineCount,
                languageId: document.languageId
            });
        }
    });

    // Check for currently open clinerules files
    vscode.workspace.textDocuments.forEach(document => {
        if (isClinerRulesFile(document.uri)) {
            const ruleName = getRuleName(document.uri.fsPath);
            logInteraction(ruleName, 'already_open', {
                lineCount: document.lineCount,
                languageId: document.languageId
            });
        }
    });

    // Register commands
    const pingCommand = vscode.commands.registerCommand('clinerules.ping', async () => {
        const isRunning = await pingServer();
        
        if (isRunning) {
            vscode.window.showInformationMessage('ClinerRules Logger server is running');
        } else {
            vscode.window.showWarningMessage('ClinerRules Logger server is not running');
        }
    });

    const logManualCommand = vscode.commands.registerCommand('clinerules.logManual', async () => {
        // Show a quick pick to select a rule
        let ruleName = await vscode.window.showInputBox({
            placeHolder: 'Enter rule name (e.g. 05-new-task)',
            prompt: 'Rule Name'
        });

        if (!ruleName) {
            return;
        }

        // Show a quick pick to select an interaction type
        const interactionType = await vscode.window.showQuickPick([
            { label: 'read', description: 'Log a read interaction' },
            { label: 'execute', description: 'Log an execution interaction' },
            { label: 'validate', description: 'Log a validation interaction' }
        ], { placeHolder: 'Select interaction type' });

        if (!interactionType) {
            return;
        }

        // Get component name for 'execute' interaction
        let componentName = null;
        if (interactionType.label === 'execute') {
            componentName = await vscode.window.showInputBox({
                placeHolder: 'Enter component name (optional)',
                prompt: 'Component Name'
            });
        }

        // Log the interaction or execution
        let result;
        if (interactionType.label === 'execute') {
            result = await logRuleExecution(ruleName, componentName);
        } else {
            result = await logInteraction(ruleName, interactionType.label);
        }

        if (result && result.success) {
            vscode.window.showInformationMessage(
                `Successfully logged ${interactionType.label} interaction for ${ruleName}`
            );
        } else {
            vscode.window.showErrorMessage(
                `Failed to log interaction: ${result ? result.error : 'Unknown error'}`
            );
        }
    });

    const showRecentCommand = vscode.commands.registerCommand('clinerules.showRecent', async () => {
        const interactions = await getRecentInteractions(20);
        
        if (!interactions || interactions.length === 0) {
            vscode.window.showInformationMessage('No recent interactions found');
            return;
        }

        // Create a new output channel to display the interactions
        const outputChannel = vscode.window.createOutputChannel('ClinerRules Logger');
        outputChannel.clear();
        
        // Format and display the interactions
        outputChannel.appendLine('Recent ClinerRules Interactions:');
        outputChannel.appendLine('-----------------------------');
        
        interactions.forEach(interaction => {
            const time = new Date(interaction.interaction_time).toLocaleString();
            outputChannel.appendLine(
                `[${time}] ${interaction.rule_name}: ${interaction.interaction_type} (via ${interaction.application})`
            );
            
            if (interaction.metadata && Object.keys(interaction.metadata).length > 0) {
                outputChannel.appendLine(`  Metadata: ${JSON.stringify(interaction.metadata, null, 2)}`);
            }
            
            outputChannel.appendLine('');
        });
        
        outputChannel.show();
    });

    // Register event listeners and commands with extension context
    context.subscriptions.push(
        fileOpenListener,
        fileSaveListener,
        fileCloseListener,
        pingCommand,
        logManualCommand,
        showRecentCommand
    );

    // Add a status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'clinerules.ping';
    statusBarItem.text = '$(database) ClinerRules';
    statusBarItem.tooltip = 'ClinerRules Logger';
    statusBarItem.show();
    
    context.subscriptions.push(statusBarItem);

    // Log extension activation
    logInteraction('vscode_extension', 'activated', {
        vscode_version: vscode.version,
        extension_version: '1.0.0'
    });

    // Return the extension API
    return {
        logInteraction,
        logRuleExecution,
        getRecentInteractions,
        pingServer,
        config
    };
}

/**
 * Called when the extension is deactivated
 */
function deactivate() {
    // Log extension deactivation
    logInteraction('vscode_extension', 'deactivated').catch(error => {
        console.error('Failed to log deactivation:', error);
    });
}

module.exports = {
    activate,
    deactivate
};
