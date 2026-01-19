'use client';

import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import { Send, MapPin, Loader2 } from 'lucide-react';
import ChatMessage from './ChatMessage';
import SafetyReport from './SafetyReport';

export default function ChatInterface({
    onLocationRequest,
    userLocation,
    safetyData,
    isLoadingSafety,
    mapThreats,
    onSafetyCheck
}) {
    const [messages, setMessages] = useState([
        {
            id: '1',
            type: 'assistant',
            content: 'Welcome to CrisisNet. I can help you check for active threats and assess your safety. Try asking: "Is there an earthquake in California?" or "Are there any disasters near me?"',
            timestamp: new Date(),
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [conversationState, setConversationState] = useState('idle'); // idle, querying, awaiting_location, analyzing
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, safetyData]);

    // When user provides location, trigger safety check
    useEffect(() => {
        if (userLocation && conversationState === 'awaiting_location') {
            addMessage('system', `Location set: ${userLocation.lat.toFixed(4)}, ${userLocation.lng.toFixed(4)}`);
            addMessage('assistant', 'Analyzing your location for nearby threats and safe locations...');
            setConversationState('analyzing');
            onSafetyCheck(userLocation);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userLocation]);

    // When safety data arrives
    useEffect(() => {
        if (safetyData && conversationState === 'analyzing') {
            setConversationState('complete');
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [safetyData]);

    const addMessage = (type, content) => {
        const newMessage = {
            id: crypto.randomUUID(),
            type,
            content,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userQuery = inputValue.trim();
        setInputValue('');
        addMessage('user', userQuery);
        setIsLoading(true);

        // Simulate processing the query
        setTimeout(() => {
            // Check if query is about disasters/threats
            const threatKeywords = ['earthquake', 'fire', 'flood', 'tornado', 'hurricane', 'disaster', 'threat', 'danger', 'emergency', 'wildfire', 'tsunami'];
            const isAboutThreats = threatKeywords.some(keyword =>
                userQuery.toLowerCase().includes(keyword)
            );

            if (isAboutThreats) {
                addMessage('assistant', `I'll help you check for potential threats. To provide accurate safety information, I need to know your location.\n\nPlease either:\n• Click on the map to set your location\n• Or allow location access when prompted`);
                setConversationState('awaiting_location');
                onLocationRequest();
            } else {
                addMessage('assistant', 'I specialize in crisis awareness and safety guidance. You can ask me about:\n\n• Active disasters or emergencies in an area\n• Safety status of your current location\n• Nearby hospitals and safe locations\n• Evacuation routes if needed\n\nTry asking something like "Is there an earthquake in California?"');
            }
            setIsLoading(false);
        }, 1000);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[var(--background-secondary)]">
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-4 border-b border-[var(--border-color)]">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] flex items-center justify-center">
                    <span className="text-lg font-bold">C</span>
                </div>
                <div>
                    <h1 className="font-semibold text-lg">CrisisNet</h1>
                    <p className="text-xs text-[var(--foreground-secondary)]">Real-time crisis intelligence</p>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
                {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                ))}

                {/* Loading indicator */}
                {(isLoading || isLoadingSafety) && (
                    <div className="flex items-start gap-3 animate-fade-in">
                        <div className="w-8 h-8 rounded-full bg-[var(--background-elevated)] flex items-center justify-center flex-shrink-0">
                            <Loader2 className="w-4 h-4 animate-spin text-[var(--accent-primary)]" />
                        </div>
                        <div className="typing-indicator glass rounded-2xl">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                )}

                {/* Safety Report */}
                {safetyData && conversationState === 'complete' && (
                    <SafetyReport data={safetyData} />
                )}

                {/* Location prompt */}
                {conversationState === 'awaiting_location' && !userLocation && (
                    <div className="flex justify-center py-4 animate-slide-up">
                        <button
                            onClick={onLocationRequest}
                            className="btn-primary flex items-center gap-2 animate-pulse-soft"
                        >
                            <MapPin className="w-5 h-5" />
                            Click Map to Set Location
                        </button>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-[var(--border-color)]">
                <div className="flex items-center gap-3 bg-[var(--background-tertiary)] rounded-xl px-4 py-2 border border-[var(--border-color)] focus-within:border-[var(--accent-primary)] transition-colors">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask about safety concerns..."
                        className="flex-1 bg-transparent outline-none text-sm placeholder:text-[var(--foreground-muted)]"
                        disabled={isLoading || isLoadingSafety}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading || isLoadingSafety}
                        className={clsx(
                            'p-2 rounded-lg transition-all',
                            inputValue.trim() && !isLoading
                                ? 'bg-[var(--accent-primary)] text-white hover:bg-[var(--accent-primary-hover)]'
                                : 'bg-[var(--background-elevated)] text-[var(--foreground-muted)]'
                        )}
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </form>
        </div>
    );
}
