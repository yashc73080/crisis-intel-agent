from backend.agents.risk_assessment.main import classify_event
import sys

# Mock the event data
event_description = "Flood in Malaysia"
event_type = "FL"
location = "Malaysia"
coordinates = [101.304146, 3.2083304]

print("Running classify_event...", file=sys.stderr)
result = classify_event(event_description, event_type, location, coordinates)
print("Result:", result)
