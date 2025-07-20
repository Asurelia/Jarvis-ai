import axios, { AxiosInstance } from 'axios';
import * as WebSocket from 'ws';
import { v4 as uuidv4 } from 'uuid';

export interface JarvisResponse {
    success: boolean;
    result?: any;
    error?: string;
    timestamp: string;
}

export interface CodeContext {
    language: string;
    filename?: string;
    projectRoot?: string;
    imports?: string[];
    classes?: string[];
    functions?: string[];
}

export class JarvisClient {
    private http: AxiosInstance;
    private ws: WebSocket | null = null;
    private messageHandlers = new Map<string, (data: any) => void>();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;

    constructor(private baseUrl: string) {
        this.http = axios.create({
            baseURL: baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'JARVIS-VSCode-Extension/2.0.0'
            }
        });

        this.connectWebSocket();
    }

    private connectWebSocket() {
        const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws';
        
        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.on('open', () => {
                console.log('JARVIS WebSocket connected');
                this.reconnectAttempts = 0;
            });

            this.ws.on('message', (data: string) => {
                try {
                    const message = JSON.parse(data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            });

            this.ws.on('close', () => {
                console.log('JARVIS WebSocket disconnected');
                this.scheduleReconnect();
            });

            this.ws.on('error', (error) => {
                console.error('JARVIS WebSocket error:', error);
            });

        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.scheduleReconnect();
        }
    }

    private scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            setTimeout(() => {
                console.log(`Attempting WebSocket reconnection (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, delay);
        }
    }

    private handleWebSocketMessage(message: any) {
        const handler = this.messageHandlers.get(message.type);
        if (handler) {
            handler(message);
        }
    }

    public onMessage(type: string, handler: (data: any) => void) {
        this.messageHandlers.set(type, handler);
    }

    public async sendMessage(message: string, context?: any): Promise<JarvisResponse> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message,
                    context
                }
            });

            return response.data;
        } catch (error: any) {
            throw new Error(`Failed to send message: ${error.message}`);
        }
    }

    public async explainCode(code: string, context: CodeContext): Promise<string> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message: `Please explain this ${context.language} code:\\n\\n\`\`\`${context.language}\\n${code}\\n\`\`\``,
                    context: {
                        type: 'code_explanation',
                        language: context.language,
                        filename: context.filename
                    }
                }
            });

            return response.data.result?.result?.content || 'No explanation available';
        } catch (error: any) {
            throw new Error(`Failed to explain code: ${error.message}`);
        }
    }

    public async refactorCode(code: string, context: CodeContext): Promise<any> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message: `Please refactor this ${context.language} code to improve readability and performance:\\n\\n\`\`\`${context.language}\\n${code}\\n\`\`\`\\n\\nProvide the refactored code and explain the improvements.`,
                    context: {
                        type: 'code_refactoring',
                        language: context.language,
                        filename: context.filename
                    }
                }
            });

            const result = response.data.result?.result?.content || '';
            
            // Parse the response to extract refactored code and explanation
            const codeMatch = result.match(/```[a-zA-Z]*\\n([\\s\\S]*?)\\n```/);
            const refactoredCode = codeMatch ? codeMatch[1] : code;
            
            return {
                refactoredCode,
                explanation: result,
                improvements: []
            };
        } catch (error: any) {
            throw new Error(`Failed to refactor code: ${error.message}`);
        }
    }

    public async generateTests(code: string, context: { language: string; framework: string }): Promise<any> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message: `Generate comprehensive unit tests for this ${context.language} code using ${context.framework}:\\n\\n\`\`\`${context.language}\\n${code}\\n\`\`\`\\n\\nInclude edge cases and error scenarios.`,
                    context: {
                        type: 'test_generation',
                        language: context.language,
                        framework: context.framework
                    }
                }
            });

            const result = response.data.result?.result?.content || '';
            const codeMatch = result.match(/```[a-zA-Z]*\\n([\\s\\S]*?)\\n```/);
            
            return {
                code: codeMatch ? codeMatch[1] : '// No tests generated',
                explanation: result
            };
        } catch (error: any) {
            throw new Error(`Failed to generate tests: ${error.message}`);
        }
    }

    public async optimizeCode(code: string, context: { language: string; target: string }): Promise<any> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message: `Optimize this ${context.language} code for ${context.target}:\\n\\n\`\`\`${context.language}\\n${code}\\n\`\`\`\\n\\nProvide optimized version and explain the improvements.`,
                    context: {
                        type: 'code_optimization',
                        language: context.language,
                        target: context.target
                    }
                }
            });

            const result = response.data.result?.result?.content || '';
            const codeMatch = result.match(/```[a-zA-Z]*\\n([\\s\\S]*?)\\n```/);
            
            return {
                optimizedCode: codeMatch ? codeMatch[1] : code,
                explanation: result,
                improvements: []
            };
        } catch (error: any) {
            throw new Error(`Failed to optimize code: ${error.message}`);
        }
    }

    public async getCodeCompletion(prefix: string, context: CodeContext): Promise<any[]> {
        try {
            const response = await this.http.post('/tools/ai_chat', {
                parameters: {
                    message: `Provide intelligent code completion suggestions for this ${context.language} code prefix:\\n\\n\`\`\`${context.language}\\n${prefix}\\n\`\`\`\\n\\nReturn only the completion suggestions as JSON array.`,
                    context: {
                        type: 'code_completion',
                        language: context.language,
                        filename: context.filename
                    }
                }
            });

            // Try to parse JSON from response
            const result = response.data.result?.result?.content || '[]';
            try {
                return JSON.parse(result);
            } catch {
                // If not JSON, create basic suggestions
                return [{
                    text: result.trim(),
                    kind: 'text',
                    detail: 'JARVIS AI Suggestion'
                }];
            }
        } catch (error: any) {
            console.error('Code completion error:', error);
            return [];
        }
    }

    public async executeSystemCommand(command: string): Promise<JarvisResponse> {
        try {
            const response = await this.http.post('/tools/system_type_text', {
                parameters: { text: command }
            });

            return response.data;
        } catch (error: any) {
            throw new Error(`Failed to execute system command: ${error.message}`);
        }
    }

    public async takeScreenshot(): Promise<JarvisResponse> {
        try {
            const response = await this.http.post('/tools/system_screenshot', {
                parameters: {}
            });

            return response.data;
        } catch (error: any) {
            throw new Error(`Failed to take screenshot: ${error.message}`);
        }
    }

    public async createTerminalSession(workingDir?: string): Promise<string> {
        try {
            const response = await this.http.post('/tools/terminal_create_session', {
                parameters: { working_dir: workingDir }
            });

            return response.data.result?.session_id || '';
        } catch (error: any) {
            throw new Error(`Failed to create terminal session: ${error.message}`);
        }
    }

    public async executeTerminalCommand(sessionId: string, command: string): Promise<JarvisResponse> {
        try {
            const response = await this.http.post('/tools/terminal_execute', {
                parameters: {
                    session_id: sessionId,
                    command
                }
            });

            return response.data;
        } catch (error: any) {
            throw new Error(`Failed to execute terminal command: ${error.message}`);
        }
    }

    public async textToSpeech(text: string): Promise<JarvisResponse> {
        try {
            const response = await this.http.post('/tools/tts_speak', {
                parameters: { text }
            });

            return response.data;
        } catch (error: any) {
            throw new Error(`Failed to convert text to speech: ${error.message}`);
        }
    }

    public sendWebSocketMessage(type: string, data: any) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...data }));
        }
    }

    public disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    public async healthCheck(): Promise<boolean> {
        try {
            const response = await this.http.get('/health');
            return response.data.status === 'healthy';
        } catch {
            return false;
        }
    }
}`;