# CrisisNet AI Assistant Web Frontend Implementation Plan

## Overview

The CrisisNet AI Assistant is a real-time crisis safety web application that provides instantaneous, actionable safety information during emergency events. The application features a Chat-First interface with natural language processing to guide users from inquiry (awareness) to action (evacuation), enhanced with Map-on-Demand visualization for critical geographic context.

**Primary Goal**: Guide users from awareness ("Is there a threat?") to action ("Where do I go?") through an intuitive conversational flow.

**Target Aesthetic**: Modern, minimalist, high-contrast Dark Mode emphasizing clarity and speed during crisis situations.

## Current State Analysis

The backend system is a mature, decoupled microservices architecture with four specialized Python agents:

1. **Data Collection Agent** - Fetches disaster data from GDACS, USGS, and testing sources
2. **Risk Assessment Agent** - AI-powered threat analysis using Google Gemini 2.5 Flash
3. **Geolocation Safety Agent** - Location-based threat analysis and route planning with Google Maps
4. **Communication Agent** - Natural language intent parsing and query mapping

**Current Interface**: Command-line coordinator only - no existing web frontend implementation.

**Backend API Access**: All agents communicate via Model Context Protocol (MCP) through stdio connections. The coordinator manages agent sessions and provides the primary interface for data flow.

## Desired End State

A fully functional web application with:

- **Split-Pane Layout**: 40% Chat Interface (left), 60% Map/Data Visualization (right)
- **Conversational Workflow**: Natural language crisis inquiry through AI-powered chat
- **Real-time Map Integration**: Interactive map with threat markers and safe locations
- **Location-based Safety Analysis**: Comprehensive threat assessment based on user location
- **Route Planning**: Safe evacuation route computation with threat avoidance
- **Responsive Design**: Optimized for desktop and mobile crisis scenarios

---

## Frontend Architecture Specification

### Technology Stack

**Frontend Framework**: React 18+ with TypeScript using Vite
- Vite for development setup and ultra-fast builds (optimized for crisis response)
- React Router v6 for navigation and code splitting
- State management with React Context + useReducer (Zustand optional for complex state)
- TanStack Query for API state management and caching
- Axios for HTTP communication with retry logic and interceptors

**UI Component Library**: Headless UI with custom styling
- Use CSS-in-JS (styled-components) or Tailwind CSS for dark theme
- Custom components following the specified aesthetic
- Accessibility focused (WCAG 2.1 AA compliance for crisis scenarios)

**Map Integration**: Google Maps JavaScript API
- Dark/silver map theme for high contrast and crisis visibility
- Custom markers for threats, safe locations, and user position
- Real-time marker updates and route visualization
- Google Places API integration for location search
- Google Directions API for evacuation route planning

**Styling Approach**: Custom CSS with CSS Variables
- CSS variables for consistent dark theme colors
- High contrast design principles
- Responsive breakpoints for mobile optimization

### Project Structure

```
crisisnet-frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── ChatInterface/
│   │   │   ├── ChatLog.tsx
│   │   │   ├── ChatBubble.tsx
│   │   │   ├── DataCard.tsx
│   │   │   ├── LocationSetter.tsx
│   │   │   ├── ActionPrompt.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── MapVisualization/
│   │   │   ├── InteractiveMap.tsx
│   │   │   ├── MapMarkers.tsx
│   │   │   ├── LocationPinpoint.tsx
│   │   │   └── SafeLocationList.tsx
│   │   └── Layout/
│   │       ├── SplitPane.tsx
│   │       ├── Header.tsx
│   │       └── LoadingState.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts (if implemented)
│   │   └── types.ts
│   ├── hooks/
│   │   ├── useChat.ts
│   │   ├── useLocation.ts
│   │   ├── useSafetyCheck.ts
│   │   └── useRoutePlanning.ts
│   ├── context/
│   │   ├── AppContext.tsx
│   │   └── ChatContext.tsx
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── styles/
│   │   ├── globals.css
│   │   ├── variables.css
│   │   └── components/
│   ├── App.tsx
│   └── index.tsx
├── package.json
├── tsconfig.json
└── README.md
```

---

## Component Specification

### Left Pane (Chat Interface) - 40% Width

#### File: src/components/ChatInterface/ChatLog.tsx
**Purpose**: Scrollable conversation history container
**Implementation**:
- Auto-scrolling to latest message
- Maintains scroll position during loading
- Dark background (#1a1a1a) with subtle borders
- Maximum height with overflow handling

#### File: src/components/ChatInterface/ChatBubble.tsx
**Purpose**: Individual message display component
**Props**:
- `type: 'user' | 'assistant' | 'system'`
- `message: string`
- `timestamp?: string`
**Visual Design**:
- User: Light gray/blue background (#2d3748), right-aligned
- Assistant: Darker gray background (#2a2a2a), left-aligned
- System: Yellow accent (#ed8936), centered for notifications
- Rounded corners (8px), padding: 12px 16px
- Font: 14px, sans-serif, white text

#### File: src/components/ChatInterface/DataCard.tsx
**Purpose**: Structured display of AI analysis results
**Props**:
- `riskScore: number (0-100)`
- `severity: 'Safe' | 'Caution' | 'Danger' | 'Critical'`
- `reasoning: string`
- `threats?: ThreatData[]`
**Visual Design**:
- Card background: #2a2a2a, border: 1px solid #4a5568
- Header with severity color coding:
  - Safe: Green (#48bb78)
  - Caution: Yellow (#ed8936)
  - Danger: Orange (#f56500)
  - Critical: Red (#e53e3e)
- Risk Score: Large text (32px) with severity color
- Reasoning: Smaller text (14px) below score
- Box shadow for elevation

#### File: src/components/ChatInterface/LocationSetter.tsx
**Purpose**: User location confirmation interface
**Implementation**:
- Full-width overlay within chat pane
- High contrast message: "Please confirm your location"
- Action button: "SET LOCATION ON MAP" (blue #3182ce)
- Pulsing animation on button to draw attention
- Disabled state after location is confirmed

#### File: src/components/ChatInterface/ActionPrompt.tsx
**Purpose**: Interactive prompts for next user actions
**Props**:
- `message: string`
- `actionText: string`
- `onAction: () => void`
**Visual Design**:
- Message text: 16px, white
- Action button: Full width, blue background (#3182ce)
- Hover state: Darker blue (#2c5aa0)
- Loading state: Shows spinner, text changes to "Processing..."
- Disabled state: Gray background (#718096)

#### File: src/components/ChatInterface/ChatInput.tsx
**Purpose**: User input field always visible at bottom of left pane
**Features**:
- Text input with placeholder ("Ask about safety concerns...")
- Send button (right side, blue icon)
- Microphone icon (left side, optional voice input)
- Enter key submits form
- Multi-line support with Ctrl+Enter for new lines
- Disabled during API calls
**Visual Design**:
- Fixed position at bottom of chat pane
- Background: #2a2a2a, border-top: 1px solid #4a5568
- Input field: White text, #4a5568 placeholder
- Button: Blue (#3182ce) with white send icon

### Right Pane (Map/Data Visualization) - 60% Width

#### File: src/components/MapVisualization/InteractiveMap.tsx
**Purpose**: Interactive map component with dark theme
**Implementation**:
- Uses Leaflet with dark tile layer (CartoDB Dark Matter)
- Initial view: Centered on North America (zoom 3)
- User location: Centered on confirmed coordinates (zoom 10-12)
- Custom markers (defined in MapMarkers.tsx)
- Route polylines for evacuation planning
- Map controls disabled during location pinpoint mode

#### File: src/components/MapVisualization/MapMarkers.tsx
**Purpose**: Custom map markers and icons
**Marker Types**:
- **User Location**: Blue pulsating circle, larger size (25px)
  - Animation: CSS pulse effect every 2 seconds
  - Coordinates: From user location confirmation
- **Threat Locations**: Lightning bolt icon, color-coded by severity
  - Critical: Red (#e53e3e), 20px
  - Caution: Yellow (#ed8936), 18px
  - Clickable: Shows threat details in popup
- **Safe Locations**: Shield/Cross icons, always green (#48bb78)
  - Hospitals: Red cross icon, 18px
  - Police: Shield icon, 18px
  - Shelters: House icon, 18px
  - Clickable: Shows location details in popup

#### File: src/components/MapVisualization/LocationPinpoint.tsx
**Purpose**: Location selection overlay for map
**Implementation**:
- Full-screen overlay on map when location confirmation needed
- High-contrast text: "CLICK TO SET LOCATION"
- Pulsing animated circle at map center
- Click handler captures map coordinates
- Automatically closes after successful selection
- Esc key to cancel

#### File: src/components/MapVisualization/SafeLocationList.tsx
**Purpose**: Scrollable list of safe locations below map
**Props**:
- `locations: SafeLocation[]`
- `onLocationSelect: (location: SafeLocation) => void`
**Visual Design**:
- Background: #1a1a1a, border: 1px solid #4a5568
- Max height: 200px with vertical scroll
- Location items: Padding 12px, hover background #2a2a2a
- Location format:
  - Name (bold, white)
  - Type (small, gray #a0aec0)
  - Distance (right-aligned, green #48bb78)
- Click handler highlights corresponding map marker

---

## Backend Integration Specification

### API Communication Layer

#### File: src/services/api.ts
**Purpose**: Communication layer with backend coordinator
**Implementation**:
- Dual communication approach: REST API for actions, WebSocket for real-time updates
- REST API wrapper around existing coordinator for user-initiated actions
- WebSocket gateway for real-time threat monitoring and status updates
- Message queue for handling asynchronous responses
- Error handling and retry logic with exponential backoff
- Timeout management for agent calls (30s default)
- Connection state management for WebSocket resilience

**API Endpoints**:
- `POST /api/intent/parse` - Communication Agent intent parsing
- `POST /api/events/query` - Data Collection Agent event retrieval
- `POST /api/events/persist` - Data Collection Agent persistence
- `POST /api/risk/classify` - Risk Assessment Agent classification
- `POST /api/safety/check` - Geolocation Safety Agent comprehensive analysis
- `POST /api/routes/compute` - Geolocation Safety Agent route planning

#### File: src/services/types.ts
**Purpose**: TypeScript type definitions for API communication
**Types**:
```typescript
interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  message: string;
  timestamp: Date;
  data?: any;
}

interface Location {
  coordinates: [number, number]; // [lat, lon]
  address?: string;
}

interface ThreatData {
  id: string;
  type: string;
  coordinates: [number, number];
  distanceKm: number;
  riskScore: number;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  description: string;
}

interface SafeLocation {
  id: string;
  name: string;
  type: 'hospital' | 'police' | 'shelter';
  coordinates: [number, number];
  distanceKm: number;
  address?: string;
}

interface SafetyAnalysis {
  overallStatus: 'safe' | 'caution' | 'danger';
  recommendation: string;
  threats: {
    threatCount: number;
    threats: ThreatData[];
  };
  nearbyHospitals: SafeLocation[];
  nearbyPolice: SafeLocation[];
  nearbyShelters: SafeLocation[];
}

interface RoutePlan {
  routes: Array<{
    routeIndex: number;
    summary: string;
    distanceText: string;
    durationText: string;
    threatAnalysis: {
      safetyLevel: 'safe' | 'caution' | 'danger';
      minThreatDistanceKm?: number;
    };
  }>;
  recommendedRouteIndex: number;
  routeCount: number;
}
```

### Conversation Flow Management

#### File: src/hooks/useChat.ts
**Purpose**: Chat state management and conversation flow
**State**:
- `messages: ChatMessage[]`
- `isLoading: boolean`
- `currentStep: 'inquiry' | 'location_confirmation' | 'safety_analysis' | 'route_planning' | 'complete'`
- `userLocation: Location | null`

**Functions**:
- `sendMessage(message: string)` - Handle user input
- `confirmLocation(coordinates: [number, number])` - Confirm user location
- `requestRoute(destination: [number, number])` - Plan evacuation route
- `resetConversation()` - Start new conversation

#### File: src/hooks/useLocation.ts
**Purpose**: Location management and geolocation services
**Features**:
- Browser geolocation API integration
- Manual location selection via map
- Location validation and formatting
- Coordinate conversion utilities

#### File: src/hooks/useSafetyCheck.ts
**Purpose**: Safety analysis integration with backend
**Functions**:
- `checkSafety(location: Location)` - Comprehensive safety analysis
- `monitorThreats(location: Location)` - Real-time threat monitoring
- `getNearbySafeLocations(location: Location)` - Find safe locations

#### File: src/hooks/useRoutePlanning.ts
**Purpose**: Route planning and evacuation guidance
**Functions**:
- `planRoute(origin: Location, destination: Location)` - Calculate safe routes
- `analyzeRouteSafety(route: any)` - Analyze route threat exposure
- `displayRoute(route: any)` - Show route on map

---

## User Workflow Implementation

### Step 1: Initial Inquiry
**User Action**: User types natural language query about potential threats
**Frontend Action**:
- Display user message in chat log
- Show "Searching for events..." loading state
- Map remains in default view (North America centered)
**Backend Integration**: POST to `/api/intent/parse` with user query

### Step 2: System Response (Event Found)
**Frontend Action**:
- Display AI response with event findings
- Center map on event's general location (zoom 8-10)
- Show threat preview markers on map
**Backend Integration**: Use parsed intent to call `/api/events/query`

### Step 3: Location Confirmation
**Frontend Action**:
- Display LocationSetterCard: "Please confirm your location for safety assessment"
- Show LocationPinpointTool overlay on map with "CLICK TO SET LOCATION" text
- Pulsing animation at map center
**User Interaction**: User clicks map to set precise [lat, lon] coordinates
**Frontend Response**:
- Remove pinpoint overlay
- Add User Location marker (blue pulsating dot)
- Show "Location confirmed. Running comprehensive safety check..." message

### Step 4: Safety Check and Analysis
**Frontend Action**:
- Display loading state in chat
- Call `/api/safety/check` with user coordinates
**Backend Integration**: Comprehensive threat and safe location analysis
**Frontend Response**:
- Display DataCard with Risk Score (0-100) and Severity (color-coded)
- Add Threat Markers to map (lightning bolts, color-coded)
- Add Safe Location Markers to map (shields/crosses, green)
- Populate SafeLocationList below map
- Update map to show all markers with appropriate zoom level

### Step 5: Action Recommendation
**Frontend Action**:
- Display ActionPrompt: "Threats detected. Plan a route to the nearest Safe Location?"
- Show "Plan Route" button
- Map remains active with all markers visible

### Step 6: Route Planning
**User Action**: Click "Plan Route" button
**Frontend Action**:
- Show loading state: "Computing safest evacuation route..."
- Call `/api/routes/compute` with user location and nearest safe location
**Backend Integration**: Calculate routes with threat avoidance
**Frontend Response**:
- Display Route Summary Data Card with route options
- Draw recommended route as highlighted polyline on map
- Show route distance, duration, and safety analysis

### Step 7: Follow-up Support
**Frontend Action**:
- Continue conversation flow for additional questions
- Maintain route visualization on map
- Provide contextual safety information based on user queries

---

## Visual Design System

### Color Palette (Dark Theme)
- **Primary Background**: #1a1a1a (very dark gray)
- **Secondary Background**: #2a2a2a (dark gray)
- **Tertiary Background**: #2d3748 (medium gray)
- **Border Color**: #4a5568 (gray)
- **Primary Text**: #ffffff (white)
- **Secondary Text**: #a0aec0 (light gray)
- **Accent Blue**: #3182ce (primary action)
- **Hover Blue**: #2c5aa0 (primary action hover)
- **Success Green**: #48bb78 (safe status)
- **Warning Yellow**: #ed8936 (caution status)
- **Warning Orange**: #f56500 (danger status)
- **Danger Red**: #e53e3e (critical threat)
- **Disabled Gray**: #718096

### Typography
- **Font Family**: Inter, -apple-system, BlinkMacSystemFont, sans-serif
- **Base Size**: 14px
- **Large Text**: 32px (risk scores)
- **Medium Text**: 16px (messages, headings)
- **Small Text**: 12px (metadata, timestamps)

### Spacing System
- **XS**: 4px (padding inside components)
- **SM**: 8px (between related elements)
- **MD**: 12px (between sections)
- **LG**: 16px (component padding)
- **XL**: 20px (container padding)

### Animation Guidelines
- **Loading States**: Simple spinners, no complex animations
- **Pulsing Effects**: 2-second intervals, subtle opacity changes
- **Hover States**: 0.2s ease transitions
- **State Changes**: 0.3s ease transitions
- **Map Animations**: Smooth pan and zoom (0.5s ease)

---

## Responsive Design Specifications

### Desktop (> 768px)
- Split-pane layout maintained
- Left pane: 40% width (minimum 320px)
- Right pane: 60% width (minimum 400px)
- SafeLocationList: Max height 200px, scrollable

### Tablet (768px - 1024px)
- Split-pane layout maintained
- Left pane: 35% width (minimum 280px)
- Right pane: 65% width
- Compact chat bubbles (reduced padding)
- Smaller map markers

### Mobile (< 768px)
- **Smart Context-Aware Layout**: Dynamic interface based on conversation state
- **Initial State**: Chat pane prominent (70% height), map minimized (30%)
- **Location Setting**: Map pane prominent (70% height), chat minimized (30%)
- **Safety Analysis**: 50/50 split with both chat and map visible
- **Route Planning**: Map pane full screen with route overlay, chat minimized
- **Emergency Context**: Map prioritized with floating chat bubble for quick questions
- SafeLocationList: Slide-up panel from bottom (max height 60% viewport)
- Touch-optimized buttons (minimum 44px height, 8px padding)
- Contextual toggle button to manually switch focus between chat and map
- Swipe gestures to quickly switch between interfaces
- Floating action button for immediate location confirmation

---

## Performance and Reliability Requirements

### Loading States
- Initial app load: Show application logo and loading spinner
- API calls: Show contextual loading messages
- Map loading: Show map skeleton with placeholder
- Route computation: Show progress indicator

### Error Handling
- Network errors: Retry button with error message
- Location errors: Manual location entry fallback
- Map loading errors: Simplified text-based directions
- API timeouts: Clear error messages with retry options

### Accessibility
- Keyboard navigation throughout application
- Screen reader compatibility for chat messages
- High contrast compliance (WCAG AA)
- Focus indicators on interactive elements
- ARIA labels for map markers and controls

### Security Considerations
- No location data stored locally beyond session
- Secure HTTPS communication with backend
- Input sanitization for user messages
- XSS prevention in chat message rendering

---

## Testing Requirements

### Manual Testing Checklist

#### Test 1: Crisis Inquiry Workflow
1. Navigate to application
2. Enter natural language query: "Is there an earthquake in California?"
3. Verify intent parsing works correctly
4. Confirm map centers on appropriate region
5. Verify location confirmation prompt appears

#### Test 2: Location Setting
1. Click location confirmation button
2. Verify pinpoint overlay appears on map
3. Click on map to set location
4. Confirm blue user marker appears at selected location
5. Verify "Location confirmed" message appears

#### Test 3: Safety Analysis
1. Wait for safety analysis to complete
2. Verify DataCard displays with Risk Score and Severity
3. Confirm threat markers appear on map (if threats exist)
4. Verify safe location markers appear on map
5. Confirm SafeLocationList populates below map

#### Test 4: Route Planning
1. Click "Plan Route" button when threats detected
2. Verify loading state shows "Computing route..."
3. Confirm route polyline appears on map
4. Verify Route Summary Data Card displays
5. Test route highlight selection

#### Test 5: Mobile Responsiveness
1. Test on mobile device or browser simulation
2. Verify stacked layout (chat over map)
3. Test touch interactions on map
4. Verify chat functionality works
5. Test route planning on mobile

#### Test 6: Error Handling
1. Test with network disconnected
2. Test invalid location entry
3. Test rapid successive user inputs
4. Test browser back button behavior
5. Verify all error states are user-friendly

---

## Deployment and Configuration

### Deployment Architecture
**Frontend Hosting**: Separate static hosting (Vercel, Netlify, or similar)
- CORS configuration to communicate with backend API
- HTTPS enforcement for security
- CDN distribution for global performance
- Continuous deployment from Git repository
- Environment-specific configurations

**Backend Integration**: REST API wrapper around existing coordinator
- New FastAPI endpoints to serve web frontend requests
- CORS middleware configured for frontend domain
- Rate limiting and security headers
- WebSocket gateway for real-time updates

### Environment Variables
- `REACT_APP_API_BASE_URL`: Backend coordinator API URL
- `REACT_APP_WEBSOCKET_URL`: WebSocket connection URL
- `REACT_APP_GOOGLE_MAPS_API_KEY`: Google Maps JavaScript API key
- `REACT_APP_DEFAULT_MAP_CENTER`: Default map center coordinates ([lat, lon])
- `REACT_APP_DEFAULT_MAP_ZOOM`: Default map zoom level (3 for continent view)
- `REACT_APP_EMERGENCY_CONTACT`: Emergency contact number for display
- `REACT_APP_VERSION`: Application version for debugging

### Build Configuration
- Production optimizations enabled
- Source maps disabled for security (production only)
- Bundle size optimization for mobile crisis scenarios
- Service worker for basic offline capability
- Critical CSS inlining for faster initial load
- Image optimization and lazy loading
- Code splitting by route for performance

### Security Configuration
- Content Security Policy (CSP) headers
- HTTPS only communication
- API rate limiting per user/session
- Input sanitization for all user inputs
- XSS prevention in chat rendering
- Secure cookie handling for session management

### Browser Compatibility
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- Geolocation API required for location services
- WebGL required for Google Maps rendering
- ES2017+ JavaScript support
- Progressive enhancement for older browsers
- Fallback messaging for unsupported features
