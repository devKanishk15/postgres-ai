import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, Activity } from 'lucide-react';
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
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, loading]);

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

        try {
            const data = await chatWithAgent(input);
            const assistantMessage: Message = {
                role: 'assistant',
                content: data.analysis,
                timestamp: data.timestamp,
                iterations: data.iterations,
                tool_calls: data.tool_calls,
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            console.error('Chat error:', err);
            const errorMessage: Message = {
                role: 'assistant',
                content: "I'm sorry, I encountered an error while analyzing the database. Please check if the backend is running.",
                timestamp: new Date().toISOString(),
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen overflow-hidden">
            {/* Messages Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar pt-10"
            >
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50">
                        <div className="p-4 bg-white/5 rounded-full">
                            <Sparkles className="w-12 h-12 text-blue-400" />
                        </div>
                        <div>
                            <h3 className="text-xl font-medium text-white">How can I help you today?</h3>
                            <p className="text-sm text-white/60 mt-2 max-w-sm">
                                Ask me about database performance, connection issues, or system health.
                            </p>
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={cn(
                            "flex gap-4 max-w-4xl mx-auto group animate-in slide-in-from-bottom-2 duration-300",
                            msg.role === 'user' ? "flex-row-reverse" : "flex-row"
                        )}
                    >
                        <div className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border",
                            msg.role === 'user' ? "bg-white/10 border-white/20" : "bg-blue-500/10 border-blue-500/20"
                        )}>
                            {msg.role === 'user' ? <User className="w-5 h-5 text-white/80" /> : <Bot className="w-5 h-5 text-blue-400" />}
                        </div>

                        <div className={cn(
                            "flex flex-col space-y-2 max-w-[85%]",
                            msg.role === 'user' ? "items-end" : "items-start"
                        )}>
                            <div className={cn(
                                "px-5 py-4 rounded-2xl text-sm leading-relaxed",
                                msg.role === 'user'
                                    ? "bg-blue-600 text-white rounded-tr-none"
                                    : "bg-white/5 border border-white/10 text-white/90 rounded-tl-none"
                            )}>
                                <div className="prose prose-invert prose-sm max-w-none">
                                    <ReactMarkdown>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>

                                {msg.tool_calls && msg.tool_calls.length > 0 && (
                                    <div className="mt-4 pt-4 border-t border-white/10 space-y-2">
                                        <div className="text-[10px] text-white/30 font-semibold uppercase tracking-widest flex items-center gap-2">
                                            <Activity className="w-3 h-3" />
                                            Tools Used ({msg.iterations} iterations)
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {msg.tool_calls.map((tc, idx) => (
                                                <div key={idx} className="text-[10px] bg-white/5 px-2 py-1 rounded border border-white/5 text-white/50">
                                                    {tc.tool}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                            <span className="text-[10px] text-white/20 font-medium px-2">
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex gap-4 max-w-4xl mx-auto flex-row animate-in fade-in duration-500">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border bg-blue-500/10 border-blue-500/20">
                            <Bot className="w-5 h-5 text-blue-400" />
                        </div>
                        <div className="px-5 py-4 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
                            <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                            <span className="text-sm text-white/40 font-medium">Analyzing Postgres Metrics...</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-6 pt-0 max-w-4xl mx-auto w-full">
                <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl blur opacity-25 group-focus-within:opacity-50 transition duration-1000"></div>
                    <div className="relative flex items-center bg-black/40 border border-white/10 rounded-2xl p-2 pl-4 focus-within:border-white/20 transition-all shadow-2xl backdrop-blur-xl">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Query your database metrics..."
                            className="flex-1 bg-transparent border-none outline-none text-white text-sm py-2 placeholder:text-white/20"
                        />
                        <button
                            onClick={handleSend}
                            disabled={loading || !input.trim()}
                            className="p-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:bg-white/5 text-white rounded-xl transition-all shadow-lg shadow-blue-600/20"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </div>
                </div>
                <p className="text-[10px] text-center text-white/20 mt-4 font-medium uppercase tracking-widest">
                    Powered by AI • PostgreSQL Diagnostics
                </p>
            </div>
        </div>
    );
};
