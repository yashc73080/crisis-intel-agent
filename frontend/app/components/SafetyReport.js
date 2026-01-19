'use client';

import { Shield, AlertTriangle, Hospital, MapPin, Navigation } from 'lucide-react';
import clsx from 'clsx';

export default function SafetyReport({ data }) {
    if (!data) return null;

    const { overall_status, recommendation, threats, nearby_hospitals } = data;

    const statusConfig = {
        safe: {
            icon: Shield,
            label: 'Safe',
            className: 'badge-safe',
            bgClass: 'bg-[var(--status-safe-bg)]',
            borderClass: 'border-[rgba(34,197,94,0.3)]',
        },
        caution: {
            icon: AlertTriangle,
            label: 'Caution',
            className: 'badge-caution',
            bgClass: 'bg-[var(--status-caution-bg)]',
            borderClass: 'border-[rgba(234,179,8,0.3)]',
        },
        danger: {
            icon: AlertTriangle,
            label: 'Danger',
            className: 'badge-danger',
            bgClass: 'bg-[var(--status-danger-bg)]',
            borderClass: 'border-[rgba(239,68,68,0.3)]',
        },
    };

    const status = statusConfig[overall_status] || statusConfig.caution;
    const StatusIcon = status.icon;

    const threatList = threats?.threats || threats || [];
    const hospitalList = nearby_hospitals || [];

    return (
        <div className="animate-slide-up space-y-4">
            {/* Main Status Card */}
            <div className={clsx(
                'rounded-xl p-4 border',
                status.bgClass,
                status.borderClass
            )}>
                <div className="flex items-center gap-3 mb-3">
                    <StatusIcon className={clsx(
                        'w-6 h-6',
                        overall_status === 'safe' ? 'text-[var(--status-safe)]' :
                            overall_status === 'caution' ? 'text-[var(--status-caution)]' :
                                'text-[var(--status-danger)]'
                    )} />
                    <span className={status.className}>{status.label}</span>
                </div>

                <p className="text-sm text-[var(--foreground)] leading-relaxed">
                    {recommendation}
                </p>
            </div>

            {/* Threats Section */}
            {threatList.length > 0 && (
                <div className="card">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="w-4 h-4 text-[var(--status-danger)]" />
                        <h3 className="font-semibold text-sm">Nearby Threats ({threatList.length})</h3>
                    </div>
                    <div className="space-y-2">
                        {threatList.slice(0, 3).map((threat, index) => (
                            <div
                                key={index}
                                className="flex items-start gap-3 p-3 rounded-lg bg-[var(--background-tertiary)]"
                            >
                                <div className="w-8 h-8 rounded-full bg-[var(--status-danger-bg)] flex items-center justify-center flex-shrink-0">
                                    <AlertTriangle className="w-4 h-4 text-[var(--status-danger)]" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">
                                        {threat.event_type || threat.type || 'Unknown Threat'}
                                    </p>
                                    <p className="text-xs text-[var(--foreground-secondary)]">
                                        {threat.distance_km?.toFixed(1) || threat.distanceKm?.toFixed(1) || '?'} km away
                                        {threat.risk_score && ` • Risk: ${threat.risk_score}`}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Nearby Hospitals */}
            {hospitalList.length > 0 && (
                <div className="card">
                    <div className="flex items-center gap-2 mb-3">
                        <Hospital className="w-4 h-4 text-[var(--status-safe)]" />
                        <h3 className="font-semibold text-sm">Nearby Hospitals ({hospitalList.length})</h3>
                    </div>
                    <div className="space-y-2">
                        {hospitalList.slice(0, 3).map((hospital, index) => (
                            <div
                                key={index}
                                className="flex items-start gap-3 p-3 rounded-lg bg-[var(--background-tertiary)]"
                            >
                                <div className="w-8 h-8 rounded-full bg-[var(--status-safe-bg)] flex items-center justify-center flex-shrink-0">
                                    <Hospital className="w-4 h-4 text-[var(--status-safe)]" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">
                                        {hospital.name || 'Hospital'}
                                    </p>
                                    <p className="text-xs text-[var(--foreground-secondary)]">
                                        {hospital.distance_km?.toFixed(1) || '?'} km away
                                    </p>
                                </div>
                                <a
                                    href={`https://www.google.com/maps/dir/?api=1&destination=${hospital.coordinates?.[0]},${hospital.coordinates?.[1]}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-2 rounded-lg bg-[var(--background-elevated)] hover:bg-[var(--accent-primary)] transition-colors"
                                >
                                    <Navigation className="w-4 h-4" />
                                </a>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
