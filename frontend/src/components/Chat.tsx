import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, Activity, Square, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { chatWithAgent } from '../api';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    iterations?: number;
    tool_calls?: any[];
}

export const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, loading]);

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
            setLoading(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        const controller = new AbortController();
        abortControllerRef.current = controller;

        try {
            const data = await chatWithAgent(input, controller.signal);
            const assistantMessage: Message = {
                role: 'assistant',
                content: data.analysis,
                timestamp: data.timestamp,
                iterations: data.iterations,
                tool_calls: data.tool_calls,
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err: any) {
            if (err.name === 'AbortError' || err.code === 'ERR_CANCELED') {
                console.log('Request cancelled by user');
                const cancelledMessage: Message = {
                    role: 'assistant',
                    content: "_Analysis stopped by user._",
                    timestamp: new Date().toISOString(),
                };
                setMessages(prev => [...prev, cancelledMessage]);
            } else {
                console.error('Chat error:', err);
                const errorMessage: Message = {
                    role: 'assistant',
                    content: "I'm sorry, I encountered an error while analyzing the database. Please check if the backend is running.",
                    timestamp: new Date().toISOString(),
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleCopy = async (content: string, id: string) => {
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(content);
                setCopiedId(id);
                setTimeout(() => setCopiedId(null), 2000);
            } else {
                throw new Error("Clipboard unavailable");
            }
        } catch (err) {
            const textArea = document.createElement("textarea");
            textArea.value = content;
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            textArea.style.top = "0";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                setCopiedId(id);
                setTimeout(() => setCopiedId(null), 2000);
            } catch (fallbackErr) {
                console.error('Copy failure:', fallbackErr);
            }
            document.body.removeChild(textArea);
        }
    };

    const renderFormattedContent = (content: string) => {
        if (!content) return null;

        // Robust regex to extract a markdown table block
        // Look for lines starting with |, including header and separator
        const tableRegex = /((?:^|\n)\|[^\n]+\|[\s\n]*\|[ :\- |]+\|[\s\n]*(?:\|[^\n]+\|(?:\n|$))+)/g;

        const parts = content.split(tableRegex);

        return parts.map((part, idx) => {
            if (!part) return null;

            if (part.trim().startsWith('|') && part.includes('|:--')) {
                try {
                    const lines = part.trim().split('\n').filter(l => l.trim().startsWith('|'));
                    if (lines.length >= 2) {
                        const headers = lines[0].split('|').filter(s => s.trim() !== '').map(s => s.trim());
                        const getRowCells = (line: string) => {
                            const cells = line.split('|');
                            return cells.slice(1, -1).map(c => c.trim());
                        };

                        const rows = lines.slice(2).map(getRowCells);

                        return (
                            <div key={idx} className="overflow-x-auto my-5 rounded-xl border border-white/10 bg-[#121212] shadow-xl">
                                <table className="w-full text-[13px] border-collapse">
                                    <thead>
                                        <tr className="bg-white/5 border-b border-white/10">
                                            {headers.map((h, i) => (
                                                <th key={i} className="px-4 py-3 text-left font-bold text-white/50 uppercase text-[10px] tracking-widest whitespace-nowrap">
                                                    {h}
                                                </th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {rows.map((row, ri) => (
                                            <tr key={ri} className="hover:bg-white/[0.02] transition-colors">
                                                {row.map((cell, ci) => (
                                                    <td key={ci} className={cn(
                                                        "px-4 py-3 text-white/80",
                                                        cell.includes('OK') ? "text-green-400 font-semibold" :
                                                            cell.includes('ALERT') || cell.includes('CRITICAL') ? "text-red-400 font-semibold" : ""
                                                    )}>
                                                        {cell}
                                                    </td>
                                                ))}
                                                {Array.from({ length: headers.length - row.length }).map((_, i) => (
                                                    <td key={`empty-${i}`} className="px-4 py-3"></td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        );
                    }
                } catch (e) {
                    console.error("Manual table parse error:", e);
                }
            }

            return <ReactMarkdown key={idx}>{part}</ReactMarkdown>;
        });
    };

    return (
        <div className="flex-1 flex flex-col h-screen overflow-hidden bg-[#171717]">
            {/* Messages Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto custom-scrollbar"
            >
                <div className="max-w-3xl mx-auto w-full px-4 pt-10 pb-32">
                    {messages.length === 0 && (
                        <div className="h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
                            <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
                                <Sparkles className="w-8 h-8 text-white/80" />
                            </div>
                            <div>
                                <h3 className="text-2xl font-semibold text-white tracking-tight">How can I help you today?</h3>
                                <p className="text-sm text-white/40 mt-2 max-w-sm font-medium">
                                    Analyze PostgreSQL metrics, debug slow queries, or check system health.
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="space-y-10">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={cn(
                                    "flex gap-5 animate-in fade-in slide-in-from-bottom-2 duration-500",
                                    msg.role === 'user' ? "justify-end" : "justify-start"
                                )}
                            >
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border border-white/10 bg-[#212121]">
                                        <Bot className="w-5 h-5 text-white/80" />
                                    </div>
                                )}

                                <div className={cn(
                                    "flex flex-col space-y-2 max-w-[85%] group/message",
                                    msg.role === 'user' ? "items-end" : "items-start"
                                )}>
                                    <div className={cn(
                                        "px-4 py-2.5 rounded-2xl text-[15px] leading-relaxed relative",
                                        msg.role === 'user'
                                            ? "bg-[#262626] text-white/90 border border-white/5"
                                            : "bg-[#212121]/50 border border-white/5 text-white/90"
                                    )}>
                                        <div className="prose prose-invert max-w-none">
                                            {renderFormattedContent(msg.content)}
                                        </div>

                                        {msg.role === 'assistant' && (
                                            <div className="flex items-center gap-4 mt-2 border-t border-white/5 pt-2 opacity-0 group-hover/message:opacity-100 transition-opacity">
                                                <button
                                                    onClick={() => handleCopy(msg.content, `msg-${i}`)}
                                                    className="flex items-center gap-1.5 text-[11px] text-white/40 hover:text-white/70 font-medium transition-colors p-1"
                                                >
                                                    {copiedId === `msg-${i}` ? (
                                                        <><Check className="w-3 h-3 text-green-400" /> <span className="text-green-400">Copied!</span></>
                                                    ) : (
                                                        <><Copy className="w-3 h-3" /> Copy Result</>
                                                    )}
                                                </button>
                                            </div>
                                        )}

                                        {msg.tool_calls && msg.tool_calls.length > 0 && (
                                            <div className="mt-4 pt-4 border-t border-white/5 space-y-3">
                                                <div className="text-[10px] text-white/20 font-bold uppercase tracking-widest flex items-center gap-2">
                                                    <Activity className="w-3 h-3" />
                                                    Backend Diagnostics ({msg.iterations} iterations)
                                                </div>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {msg.tool_calls.map((tc, idx) => (
                                                        <div key={idx} className="text-[10px] bg-white/5 px-2 py-0.5 rounded border border-white/5 text-white/40 font-medium">
                                                            {tc.tool}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {msg.role === 'user' && (
                                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border border-white/10 bg-[#262626]">
                                        <User className="w-5 h-5 text-white/80" />
                                    </div>
                                )}
                            </div>
                        ))}

                        {loading && (
                            <div className="flex gap-5 animate-in fade-in duration-500">
                                <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 border border-white/10 bg-[#212121]">
                                    <Bot className="w-5 h-5 text-white/80" />
                                </div>
                                <div className="flex items-center gap-3 text-white/40">
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span className="text-sm font-medium">Thinking...</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Input Area */}
            <div className="fixed bottom-0 left-80 right-0 bg-[#171717] px-4 pb-8 pt-2">
                <div className="max-w-3xl mx-auto flex flex-col items-center">
                    {loading && (
                        <button
                            onClick={handleStop}
                            className="mb-4 flex items-center gap-2 px-4 py-2 bg-[#212121] border border-white/10 rounded-lg text-sm font-medium text-white/80 hover:bg-[#262626] transition-colors"
                        >
                            <Square className="w-3 h-3 fill-current" />
                            Stop Generation
                        </button>
                    )}

                    <div className="relative w-full">
                        <div className="relative flex items-center bg-[#212121] border border-white/10 rounded-3xl px-4 py-3 focus-within:border-white/20 transition-all shadow-xl">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !loading && handleSend()}
                                placeholder="Message PG Debugger..."
                                className="flex-1 bg-transparent border-none outline-none text-white text-[15px] placeholder:text-white/20 px-2"
                            />
                            <button
                                onClick={handleSend}
                                disabled={loading || !input.trim()}
                                className="ml-2 p-2 bg-white disabled:bg-white/10 disabled:text-white/20 text-black rounded-xl transition-all"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <p className="text-[11px] text-center text-white/20 mt-3 font-medium">
                        PostgreSQL Debug Advisor can make mistakes. Verify important info.
                    </p>
                </div>
            </div>
        </div>
    );
};
