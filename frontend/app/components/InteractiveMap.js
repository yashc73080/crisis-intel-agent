'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { APIProvider, Map, AdvancedMarker, Pin } from '@vis.gl/react-google-maps';
import clsx from 'clsx';
import { MapPin, AlertTriangle, Hospital, Crosshair, Loader2 } from 'lucide-react';

// Dark map style
const DARK_MAP_STYLE = [
    { elementType: 'geometry', stylers: [{ color: '#1a1a24' }] },
    { elementType: 'labels.text.stroke', stylers: [{ color: '#1a1a24' }] },
    { elementType: 'labels.text.fill', stylers: [{ color: '#6b7280' }] },
    { featureType: 'administrative', elementType: 'geometry.stroke', stylers: [{ color: '#374151' }] },
    { featureType: 'administrative.land_parcel', elementType: 'labels.text.fill', stylers: [{ color: '#6b7280' }] },
    { featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#22222e' }] },
    { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#6b7280' }] },
    { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#1f2937' }] },
    { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#374151' }] },
    { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#1f2937' }] },
    { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#4b5563' }] },
    { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#374151' }] },
    { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#2d3748' }] },
    { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0f172a' }] },
    { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#4b5563' }] },
];

const DEFAULT_CENTER = { lat: 39.8283, lng: -98.5795 }; // Center of USA
const DEFAULT_ZOOM = 4;

export default function InteractiveMap({
    isSelectingLocation,
    onLocationSelect,
    userLocation,
    threats = [],
    hospitals = [],
}) {
    const [mapLoaded, setMapLoaded] = useState(false);
    const [center, setCenter] = useState(DEFAULT_CENTER);
    const [zoom, setZoom] = useState(DEFAULT_ZOOM);
    const [isGettingLocation, setIsGettingLocation] = useState(false);

    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

    // Update center when user location changes
    useEffect(() => {
        if (userLocation) {
            setCenter(userLocation);
            setZoom(12);
        }
    }, [userLocation]);

    const handleMapClick = useCallback((event) => {
        if (isSelectingLocation && event.detail.latLng) {
            const { lat, lng } = event.detail.latLng;
            onLocationSelect({ lat: lat(), lng: lng() });
        }
    }, [isSelectingLocation, onLocationSelect]);

    const handleGetCurrentLocation = () => {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        setIsGettingLocation(true);
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                };
                onLocationSelect(location);
                setIsGettingLocation(false);
            },
            (error) => {
                console.error('Geolocation error:', error);
                alert('Unable to get your location. Please click on the map to set it manually.');
                setIsGettingLocation(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    };

    if (!apiKey) {
        return (
            <div className="w-full h-full flex items-center justify-center bg-[var(--background-secondary)]">
                <p className="text-[var(--foreground-muted)]">Google Maps API key not configured</p>
            </div>
        );
    }

    return (
        <div className="map-container">
            <APIProvider apiKey={apiKey}>
                <Map
                    defaultCenter={DEFAULT_CENTER}
                    defaultZoom={DEFAULT_ZOOM}
                    center={center}
                    zoom={zoom}
                    gestureHandling="greedy"
                    disableDefaultUI={true}
                    // styles={DARK_MAP_STYLE}
                    onClick={handleMapClick}
                    onTilesLoaded={() => setMapLoaded(true)}
                    className="w-full h-full"
                >
                    {/* User Location Marker */}
                    {userLocation && (
                        <AdvancedMarker position={userLocation}>
                            <div className="relative">
                                <div className="w-6 h-6 bg-[var(--accent-primary)] rounded-full border-2 border-white shadow-lg animate-pulse-glow" />
                                <div className="absolute inset-0 w-6 h-6 bg-[var(--accent-primary)] rounded-full animate-ping opacity-75" />
                            </div>
                        </AdvancedMarker>
                    )}

                    {/* Threat Markers */}
                    {threats.map((threat, index) => (
                        <AdvancedMarker
                            key={`threat-${index}`}
                            position={{
                                lat: threat.coordinates?.[0] || threat.latitude,
                                lng: threat.coordinates?.[1] || threat.longitude,
                            }}
                            title={threat.event_type || threat.type}
                        >
                            <div className="flex items-center justify-center w-8 h-8 bg-[var(--status-danger)] rounded-full border-2 border-white shadow-lg">
                                <AlertTriangle className="w-4 h-4 text-white" />
                            </div>
                        </AdvancedMarker>
                    ))}

                    {/* Hospital Markers */}
                    {hospitals.map((hospital, index) => (
                        <AdvancedMarker
                            key={`hospital-${index}`}
                            position={{
                                lat: hospital.coordinates?.[0] || hospital.latitude,
                                lng: hospital.coordinates?.[1] || hospital.longitude,
                            }}
                            title={hospital.name}
                        >
                            <div className="flex items-center justify-center w-8 h-8 bg-[var(--status-safe)] rounded-full border-2 border-white shadow-lg">
                                <Hospital className="w-4 h-4 text-white" />
                            </div>
                        </AdvancedMarker>
                    ))}
                </Map>
            </APIProvider>

            {/* Location Selection Overlay */}
            {isSelectingLocation && !userLocation && (
                <div className="map-overlay">
                    <div className="location-prompt">
                        <div className="w-16 h-16 mx-auto mb-4 bg-[var(--accent-primary)] rounded-full flex items-center justify-center animate-pulse-glow">
                            <Crosshair className="w-8 h-8 text-white" />
                        </div>
                        <h3 className="text-xl font-semibold mb-2">Set Your Location</h3>
                        <p className="text-sm text-[var(--foreground-secondary)] mb-6">
                            Click anywhere on the map to set your location, or use your device&apos;s GPS.
                        </p>
                        <div className="flex flex-col gap-3">
                            <button
                                onClick={handleGetCurrentLocation}
                                disabled={isGettingLocation}
                                className="btn-primary flex items-center justify-center gap-2"
                            >
                                {isGettingLocation ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Getting Location...
                                    </>
                                ) : (
                                    <>
                                        <MapPin className="w-5 h-5" />
                                        Use My Current Location
                                    </>
                                )}
                            </button>
                            <p className="text-xs text-[var(--foreground-muted)]">
                                Or click directly on the map
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Map Loading Indicator */}
            {!mapLoaded && (
                <div className="absolute inset-0 flex items-center justify-center bg-[var(--background-secondary)]">
                    <div className="flex items-center gap-3">
                        <Loader2 className="w-6 h-6 animate-spin text-[var(--accent-primary)]" />
                        <span className="text-[var(--foreground-secondary)]">Loading map...</span>
                    </div>
                </div>
            )}
        </div>
    );
}
