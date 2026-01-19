'use client';

import clsx from 'clsx';
import { AlertTriangle, Shield, User, Bot } from 'lucide-react';

export default function ChatMessage({ message }) {
    const { type, content, timestamp } = message;

    const isUser = type === 'user';
    const isSystem = type === 'system';

    const formatTime = (date) => {
        return new Date(date).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        });
    };

    // System messages (alerts, confirmations)
    if (isSystem) {
        return (
            <div className="flex justify-center animate-slide-up">
                <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--status-caution-bg)] border border-[rgba(234,179,8,0.3)]">
                    <AlertTriangle className="w-4 h-4 text-[var(--status-caution)]" />
                    <span className="text-sm text-[var(--status-caution)]">{content}</span>
                </div>
            </div>
        );
    }

    return (
        <div
            className={clsx(
                'flex items-start gap-3 animate-slide-up',
                isUser ? 'flex-row-reverse' : 'flex-row'
            )}
        >
            {/* Avatar */}
            <div
                className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                    isUser
                        ? 'bg-[var(--accent-primary)]'
                        : 'bg-gradient-to-br from-[var(--background-elevated)] to-[var(--background-tertiary)] border border-[var(--border-color)]'
                )}
            >
                {isUser ? (
                    <User className="w-4 h-4 text-white" />
                ) : (
                    <Bot className="w-4 h-4 text-[var(--accent-primary)]" />
                )}
            </div>

            {/* Message Bubble */}
            <div
                className={clsx(
                    'max-w-[80%] px-4 py-3 rounded-2xl',
                    isUser
                        ? 'bg-[var(--accent-primary)] text-white rounded-br-md'
                        : 'glass rounded-bl-md'
                )}
            >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{content}</p>
                <span
                    className={clsx(
                        'text-[10px] mt-2 block',
                        isUser ? 'text-white/70 text-right' : 'text-[var(--foreground-muted)]'
                    )}
                >
                    {formatTime(timestamp)}
                </span>
            </div>
        </div>
    );
}
