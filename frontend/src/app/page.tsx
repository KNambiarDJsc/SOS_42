'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    DocumentPlusIcon,
    PaperAirplaneIcon,
    XMarkIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    citations?: Array<{
        page: number;
        content_type: string;
        score: number;
    }>;
    images?: string[];
}

export default function Home() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [documentId, setDocumentId] = useState<string | null>(null);
    const [uploadedFile, setUploadedFile] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // ---------------------------
    // Upload
    // ---------------------------
    const handleFileUpload = async (file?: File) => {
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Please upload a PDF file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setIsLoading(true);

            const response = await axios.post(`${API_URL}/upload`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setDocumentId(response.data.document_id);
            setUploadedFile(file.name);

            setMessages([
                {
                    id: Date.now().toString(),
                    role: 'assistant',
                    content: `✅ **${file.name} uploaded successfully.**  
You can now ask questions about this document.`,
                    timestamp: new Date()
                }
            ]);
        } catch (err) {
            console.error(err);
            alert('Upload failed. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    // ---------------------------
    // Chat submit
    // ---------------------------
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !documentId || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await axios.post(`${API_URL}/query`, {
                query: input,
                document_id: documentId,
                top_k: 5
            });

            setMessages(prev => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: res.data.answer,
                    citations: res.data.citations,
                    images: res.data.images,
                    timestamp: new Date()
                }
            ]);
        } catch {
            setMessages(prev => [
                ...prev,
                {
                    id: (Date.now() + 1).toString(),
                    role: 'assistant',
                    content: '❌ Something went wrong. Please try again.',
                    timestamp: new Date()
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        setDocumentId(null);
        setUploadedFile(null);
    };

    // ===========================
    // RENDER
    // ===========================
    return (
        <div className="flex flex-col h-screen bg-gradient-to-br from-yellow-300 via-yellow-200 to-yellow-100">

            {/* Header */}
            <header className="bg-yellow-400 border-b-4 border-yellow-500 px-6 py-4 shadow-lg">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <h1 className="text-2xl font-black">
                        when in doubt, <span className="bg-white px-3 py-1 rounded-lg">SOS 42</span>
                    </h1>

                    {uploadedFile && (
                        <div className="flex items-center bg-white px-4 py-2 rounded-lg shadow">
                            <span className="text-sm">{uploadedFile}</span>
                            <button onClick={clearChat} className="ml-2">
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* Main */}
            <div className="flex-1 max-w-5xl mx-auto w-full p-6 flex flex-col gap-6">

                {/* Upload */}
                {!documentId && (
                    <div
                        onDrop={e => {
                            e.preventDefault();
                            setIsDragging(false);

                            const file = e.dataTransfer.files?.[0];
                            if (file) {
                                handleFileUpload(file);
                            }
                        }}
                        onDragOver={e => {
                            e.preventDefault();
                            setIsDragging(true);
                        }}
                        onDragLeave={() => setIsDragging(false)}
                        className={`border-4 border-dashed rounded-3xl p-12 text-center bg-white transition ${isDragging ? 'border-yellow-600' : 'border-yellow-400'
                            }`}
                    >
                        <DocumentPlusIcon className="w-16 h-16 mx-auto text-yellow-500" />
                        <p className="mt-4 text-lg">Upload a PDF to begin</p>

                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf"
                            className="hidden"
                            onChange={e => {
                                const file = e.target.files?.[0];
                                if (file) {
                                    handleFileUpload(file);
                                }
                            }}
                        />

                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="mt-6 px-6 py-3 bg-yellow-500 text-white rounded-xl"
                        >
                            Choose File
                        </button>
                    </div>
                )}

                {/* Chat */}
                <div
                    className={`flex-1 flex flex-col bg-white rounded-3xl shadow-xl p-6 ${!documentId ? 'opacity-40 pointer-events-none' : ''
                        }`}
                >
                    <div className="flex-1 overflow-y-auto space-y-4">
                        <AnimatePresence>
                            {messages.map(msg => (
                                <motion.div
                                    key={msg.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`max-w-3xl ${msg.role === 'user'
                                            ? 'ml-auto bg-yellow-500 text-white'
                                            : 'bg-gray-100'
                                        } rounded-2xl px-4 py-3`}
                                >
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <div ref={messagesEndRef} />
                    </div>

                    <form onSubmit={handleSubmit} className="mt-4 flex gap-3">
                        <input
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            disabled={!documentId || isLoading}
                            placeholder={
                                documentId
                                    ? 'Ask a question about your document...'
                                    : 'Upload a PDF to enable chat'
                            }
                            className="flex-1 border rounded-xl px-4 py-3"
                        />
                        <button
                            type="submit"
                            disabled={!documentId || isLoading}
                            className="bg-yellow-500 text-white rounded-xl px-4"
                        >
                            <PaperAirplaneIcon className="w-5 h-5" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
