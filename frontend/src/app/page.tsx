'use client';

import { useState, useRef, useEffect, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    DocumentPlusIcon,
    PaperAirplaneIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

/* =========================
   API CONFIG
========================= */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_URL,
    timeout: 120000, // 2 mins for PDF parsing
    maxContentLength: 20 * 1024 * 1024,
    maxBodyLength: 20 * 1024 * 1024,
});

/* =========================
   TYPES
========================= */

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    citations?: {
        page: number;
        content_type: string;
    }[];
    images?: string[];
}

/* =========================
   IMAGE GRID (ISOLATED)
========================= */

const ImageGrid = memo(({ images }: { images: string[] }) => (
    <div className="grid grid-cols-2 gap-3">
        {images.map((path, idx) => (
            <img
                key={idx}
                src={`${API_URL}${path.startsWith('/') ? '' : '/'}${path}`}
                loading="lazy"
                className="w-full h-auto rounded-lg shadow-md border-2 border-gray-200"
                alt={`Document image ${idx + 1}`}
            />
        ))}
    </div>
));
ImageGrid.displayName = 'ImageGrid';

/* =========================
   MAIN COMPONENT
========================= */

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [documentId, setDocumentId] = useState<string | null>(null);
    const [uploadedFile, setUploadedFile] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    /* =========================
       HELPERS
    ========================= */

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(scrollToBottom, [messages]);

    /* =========================
       FILE UPLOAD
    ========================= */

    const handleFileUpload = async (file: File) => {
        if (!file.name.endsWith('.pdf')) {
            alert('Only PDF files are supported');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setIsLoading(true);

            const res = await api.post('/upload', formData);

            setUploadedFile(file.name);
            setDocumentId(res.data.document_id);

            setMessages([
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: `✅ **${file.name}** uploaded successfully.  
You can now ask questions about this document.`,
                    timestamp: new Date(),
                },
            ]);
        } catch {
            alert('Failed to upload document');
        } finally {
            setIsLoading(false);
        }
    };

    /* =========================
       QUERY
    ========================= */

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !documentId || isLoading) return;

        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await api.post('/query', {
                query: input,
                document_id: documentId,
                top_k: 5,
            });

            setMessages(prev => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: res.data.answer,
                    citations: res.data.citations,
                    images: res.data.images,
                    timestamp: new Date(),
                },
            ]);
        } catch {
            setMessages(prev => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: '❌ Error processing your question.',
                    timestamp: new Date(),
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    /* =========================
       RESET
    ========================= */

    const clearChat = () => {
        setMessages([]);
        setDocumentId(null);
        setUploadedFile(null);
    };

    /* =========================
       UI
    ========================= */

    return (
        <div className="flex flex-col h-screen bg-gradient-to-br from-yellow-300 via-yellow-200 to-yellow-100">

            {/* HEADER */}
            <header className="bg-yellow-400 border-b-4 border-yellow-500 px-6 py-4 shadow-lg">
                <div className="max-w-6xl mx-auto flex justify-between items-center">
                    <h1 className="text-2xl font-black">
                        when in doubt, <span className="bg-white px-3 py-1 rounded-lg">SOS 42</span>
                    </h1>

                    {uploadedFile && (
                        <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-lg shadow">
                            <span className="text-sm font-semibold">{uploadedFile}</span>
                            <button onClick={clearChat}>
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* CONTENT */}
            <main className="flex-1 max-w-5xl mx-auto w-full p-6 flex flex-col">

                {!documentId ? (
                    /* UPLOAD */
                    <div
                        className={`flex-1 flex items-center justify-center border-4 border-dashed rounded-3xl transition ${isDragging ? 'border-yellow-600 bg-yellow-100' : 'border-yellow-400 bg-white'
                            }`}
                        onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={e => {
                            e.preventDefault();
                            setIsDragging(false);
                            handleFileUpload(e.dataTransfer.files[0]);
                        }}
                    >
                        <div className="text-center space-y-4">
                            <DocumentPlusIcon className="w-16 h-16 mx-auto text-yellow-600" />
                            <p className="text-xl font-bold">Upload a PDF</p>
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="px-6 py-3 bg-yellow-500 text-white rounded-xl"
                                disabled={isLoading}
                            >
                                {isLoading ? 'Uploading...' : 'Choose File'}
                            </button>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf"
                                hidden
                                onChange={e => e.target.files && handleFileUpload(e.target.files[0])}
                            />
                        </div>
                    </div>
                ) : (
                    /* CHAT */
                    <>
                        <div className="flex-1 overflow-y-auto bg-white rounded-3xl shadow p-6 space-y-4">
                            <AnimatePresence initial={false}>
                                {messages.map(msg => (
                                    <motion.div
                                        key={msg.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className={msg.role === 'user' ? 'text-right' : 'text-left'}
                                    >
                                        <div className={`inline-block px-5 py-4 rounded-2xl max-w-3xl ${msg.role === 'user'
                                            ? 'bg-yellow-500 text-white'
                                            : 'bg-gray-100'
                                            }`}>
                                            <ReactMarkdown>{msg.content}</ReactMarkdown>

                                            {msg.citations && msg.citations.length > 0 && (
                                                <div className="mt-3 text-xs opacity-70">
                                                    {msg.citations.map((c, i) => (
                                                        <span key={i} className="mr-2">
                                                            Page {c.page}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}

                                            {msg.images && msg.images.length > 0 && (
                                                <div className="mt-4">
                                                    <ImageGrid images={msg.images} />
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                            <div ref={messagesEndRef} />
                        </div>

                        {/* INPUT */}
                        <form onSubmit={handleSubmit} className="mt-4 flex gap-3">
                            <input
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                className="flex-1 px-5 py-4 rounded-xl border"
                                placeholder="Ask a question..."
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={isLoading}
                                className="px-6 py-4 bg-yellow-500 text-white rounded-xl"
                            >
                                <PaperAirplaneIcon className="w-5 h-5" />
                            </button>
                        </form>
                    </>
                )}
            </main>
        </div>
    );
}
