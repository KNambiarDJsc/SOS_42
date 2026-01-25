'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    DocumentPlusIcon,
    PaperAirplaneIcon,
    XMarkIcon,
    ChatBubbleBottomCenterTextIcon
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

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleFileUpload = async (file: File) => {
        if (!file.name.endsWith('.pdf')) {
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

            // Add system message
            const systemMsg: Message = {
                id: Date.now().toString(),
                role: 'assistant',
                content: `✅ Document "${file.name}" uploaded successfully! You can now ask questions about it.`,
                timestamp: new Date()
            };
            setMessages([systemMsg]);
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Failed to upload document. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFileUpload(file);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || !documentId || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await axios.post(`${API_URL}/query`, {
                query: input,
                document_id: documentId,
                top_k: 5
            });

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.data.answer,
                timestamp: new Date(),
                citations: response.data.citations,
                images: response.data.images
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            console.error('Query failed:', error);

            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: '❌ Sorry, I encountered an error processing your question. Please try again.',
                timestamp: new Date()
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const clearChat = () => {
        setMessages([]);
        setDocumentId(null);
        setUploadedFile(null);
    };

    return (
        <div className="flex flex-col h-screen bg-gradient-to-br from-yellow-300 via-yellow-200 to-yellow-100">
            {/* Header */}
            <header className="bg-yellow-400 border-b-4 border-yellow-500 px-6 py-4 shadow-lg">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-md transform rotate-12">
                            <span className="text-3xl">📚</span>
                        </div>
                        <div>
                            <h1 className="text-2xl font-black text-gray-800">
                                when in doubt, <span className="bg-white px-3 py-1 rounded-lg shadow-sm">SOS 42</span>
                            </h1>
                            <p className="text-sm text-gray-700 italic">*the adulting companion for students</p>
                        </div>
                    </div>

                    {uploadedFile && (
                        <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg shadow-md">
                            <DocumentPlusIcon className="w-5 h-5 text-yellow-600" />
                            <span className="text-sm font-medium text-gray-700">{uploadedFile}</span>
                            <button
                                onClick={clearChat}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                <XMarkIcon className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-hidden flex flex-col max-w-5xl mx-auto w-full p-6">
                {!documentId ? (
                    /* Upload Section */
                    <div className="flex-1 flex items-center justify-center">
                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            className={`w-full max-w-2xl p-12 border-4 border-dashed rounded-3xl transition-all ${isDragging
                                ? 'border-yellow-600 bg-yellow-100 scale-105'
                                : 'border-yellow-400 bg-white hover:border-yellow-600 hover:shadow-xl'
                                }`}
                        >
                            <div className="text-center space-y-6">
                                <div className="flex justify-center">
                                    <div className="w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center">
                                        <DocumentPlusIcon className="w-12 h-12 text-yellow-600" />
                                    </div>
                                </div>

                                <div>
                                    <h2 className="text-3xl font-black text-gray-800 mb-2">
                                        Upload Your PDF
                                    </h2>
                                    <p className="text-gray-600 text-lg">
                                        Drag & drop your PDF here, or click to browse
                                    </p>
                                </div>

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />

                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isLoading}
                                    className="px-8 py-4 bg-yellow-500 hover:bg-yellow-600 text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isLoading ? 'Uploading...' : 'Choose File'}
                                </button>

                                <p className="text-sm text-gray-500">
                                    Supported format: PDF • Max size: 10MB
                                </p>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Chat Section */
                    <>
                        <div className="flex-1 overflow-y-auto mb-4 space-y-4 bg-white rounded-3xl shadow-xl p-6">
                            <AnimatePresence>
                                {messages.map((message) => (
                                    <motion.div
                                        key={message.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -20 }}
                                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div
                                            className={`max-w-3xl rounded-2xl px-6 py-4 ${message.role === 'user'
                                                ? 'bg-yellow-500 text-white'
                                                : 'bg-gray-100 text-gray-800'
                                                }`}
                                        >
                                            <div className="prose prose-sm max-w-none">
                                                <ReactMarkdown>{message.content}</ReactMarkdown>
                                            </div>

                                            {/* Citations */}
                                            {message.citations && message.citations.length > 0 && (
                                                <div className="mt-4 pt-4 border-t border-gray-300">
                                                    <p className="text-xs font-semibold text-gray-600 mb-2">Sources:</p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {message.citations.map((citation, idx) => (
                                                            <span
                                                                key={idx}
                                                                className="inline-flex items-center px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium"
                                                            >
                                                                Page {citation.page} • {citation.content_type}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Images */}
                                            {message.images && message.images.length > 0 && (
                                                <div className="mt-4 pt-4 border-t border-gray-300">
                                                    <p className="text-xs font-semibold text-gray-600 mb-2">Images:</p>
                                                    <div className="grid grid-cols-2 gap-3">
                                                        {message.images.map((imagePath, idx) => (
                                                            <div key={idx} className="relative group">
                                                                <img
                                                                    src={`${API_URL}/${imagePath}`}
                                                                    alt={`Image ${idx + 1}`}
                                                                    className="w-full h-auto rounded-lg shadow-md border-2 border-gray-200 hover:border-yellow-400 transition-all"
                                                                />
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>

                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-gray-100 rounded-2xl px-6 py-4">
                                        <div className="flex items-center space-x-2">
                                            <div className="flex space-x-1">
                                                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                            </div>
                                            <span className="text-sm text-gray-500">Thinking...</span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Form */}
                        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-xl p-4">
                            <div className="flex items-center space-x-3">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask a question about your document..."
                                    disabled={isLoading}
                                    className="flex-1 px-6 py-4 bg-gray-50 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-200 transition-all disabled:opacity-50 text-gray-800"
                                />
                                <button
                                    type="submit"
                                    disabled={isLoading || !input.trim()}
                                    className="px-6 py-4 bg-yellow-500 hover:bg-yellow-600 text-white rounded-xl shadow-md hover:shadow-lg transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                                >
                                    <PaperAirplaneIcon className="w-6 h-6" />
                                </button>
                            </div>
                        </form>
                    </>
                )}
            </div>

            {/* Decorative elements */}
            <div className="fixed top-20 right-10 w-32 h-32 pointer-events-none">
                <svg viewBox="0 0 200 100" className="w-full h-full opacity-20">
                    <ellipse cx="100" cy="50" rx="80" ry="30" fill="white" stroke="#FCD34D" strokeWidth="3" />
                    <ellipse cx="100" cy="50" rx="60" ry="20" fill="white" stroke="#FCD34D" strokeWidth="2" />
                </svg>
            </div>
        </div>
    );
}