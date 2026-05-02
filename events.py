"""
Event-Driven Architecture Module
Logs all significant system events for FlowGuard AI
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class EventType(Enum):
    """Event types for system events"""
    LEAD_CREATED = "lead.created"
    WORKFLOW_STEP_UPDATED = "workflow_step.updated"
    LEAK_DETECTED = "leak.detected"
    RECOVERY_ACTION_CREATED = "recovery_action.created"
    RECOVERY_ACTION_EXECUTED = "recovery_action.executed"
    SYSTEM_EVENT = "system.event"


class Event:
    """Event model for system events"""
    def __init__(self, event_type: EventType, entity_id: str, payload: Dict):
        self.event_id = f"evt_{uuid.uuid4().hex[:12]}"
        self.event_type = event_type.value
        self.entity_id = entity_id
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.payload = payload
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "payload": self.payload
        }


# In-memory event log
events_log: List[Event] = []


def log_event(event_type: EventType, entity_id: str, payload: Dict) -> Optional[Event]:
    """
    Create and store an event
    
    Args:
        event_type: Type of event from EventType enum
        entity_id: ID of the entity related to the event
        payload: Dictionary containing event-specific data
    
    Returns:
        The created Event object
    """
    try:
        event = Event(event_type, entity_id, payload)
        events_log.append(event)
        return event
    except Exception as e:
        # Non-blocking: log error but don't crash
        print(f"Error logging event: {e}")
        return None


def get_events(limit: int = 50) -> List[Dict]:
    """
    Get recent events
    
    Args:
        limit: Maximum number of events to return (default 50)
    
    Returns:
        List of event dictionaries
    """
    return [event.to_dict() for event in events_log[-limit:]]


def get_events_by_type(event_type: EventType, limit: int = 50) -> List[Dict]:
    """
    Get events filtered by type
    
    Args:
        event_type: Type of event to filter by
        limit: Maximum number of events to return
    
    Returns:
        List of filtered event dictionaries
    """
    filtered = [event for event in events_log if event.event_type == event_type.value]
    return [event.to_dict() for event in filtered[-limit:]]


def get_events_by_entity(entity_id: str, limit: int = 50) -> List[Dict]:
    """
    Get events filtered by entity ID
    
    Args:
        entity_id: Entity ID to filter by
        limit: Maximum number of events to return
    
    Returns:
        List of filtered event dictionaries
    """
    filtered = [event for event in events_log if event.entity_id == entity_id]
    return [event.to_dict() for event in filtered[-limit:]]


def clear_events() -> None:
    """Clear all events from the event log"""
    global events_log
    events_log = []

# Made with Bob
