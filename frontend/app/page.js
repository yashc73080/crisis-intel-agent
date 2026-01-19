'use client';

import { useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import ChatInterface from './components/ChatInterface';
import { checkLocationSafety } from './services/api';

// Dynamic import for map to avoid SSR issues
const InteractiveMap = dynamic(
  () => import('./components/InteractiveMap'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-[var(--background-secondary)]">
        <div className="animate-pulse text-[var(--foreground-secondary)]">Loading map...</div>
      </div>
    )
  }
);

export default function Home() {
  const [isSelectingLocation, setIsSelectingLocation] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [safetyData, setSafetyData] = useState(null);
  const [isLoadingSafety, setIsLoadingSafety] = useState(false);
  const [threats, setThreats] = useState([]);
  const [hospitals, setHospitals] = useState([]);

  const handleLocationRequest = useCallback(() => {
    setIsSelectingLocation(true);
  }, []);

  const handleLocationSelect = useCallback((location) => {
    setUserLocation(location);
    setIsSelectingLocation(false);
  }, []);

  const handleSafetyCheck = useCallback(async (location) => {
    setIsLoadingSafety(true);
    try {
      const data = await checkLocationSafety(location.lat, location.lng, 50);
      setSafetyData(data);

      // Extract threats and hospitals for map markers
      const threatList = data.threats?.threats || data.threats || [];
      const hospitalList = data.nearby_hospitals || [];

      setThreats(threatList);
      setHospitals(hospitalList);
    } catch (error) {
      console.error('Safety check failed:', error);
      setSafetyData({
        overall_status: 'caution',
        recommendation: 'Unable to complete safety analysis. Please check your connection and try again.',
        threats: [],
        nearby_hospitals: [],
      });
    } finally {
      setIsLoadingSafety(false);
    }
  }, []);

  return (
    <div className="flex h-screen w-full overflow-hidden">
      {/* Left Pane - Chat Interface */}
      <div className="w-full md:w-[420px] lg:w-[480px] h-full flex-shrink-0 border-r border-[var(--border-color)]">
        <ChatInterface
          onLocationRequest={handleLocationRequest}
          userLocation={userLocation}
          safetyData={safetyData}
          isLoadingSafety={isLoadingSafety}
          mapThreats={threats}
          onSafetyCheck={handleSafetyCheck}
        />
      </div>

      {/* Right Pane - Interactive Map */}
      <div className="hidden md:flex flex-1 h-full">
        <InteractiveMap
          isSelectingLocation={isSelectingLocation}
          onLocationSelect={handleLocationSelect}
          userLocation={userLocation}
          threats={threats}
          hospitals={hospitals}
        />
      </div>

      {/* Mobile Map Toggle (shown when map is hidden) */}
      <div className="fixed bottom-20 right-4 md:hidden">
        <button
          onClick={() => setIsSelectingLocation(true)}
          className="btn-primary rounded-full w-14 h-14 flex items-center justify-center shadow-lg"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
