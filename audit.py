from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# ============================================================================
# AUDIT TRAIL MODULE
# ============================================================================

# In-memory audit trail storage
audit_trail_db: Dict[str, Dict[str, Any]] = {}

def generate_audit_id() -> str:
    """Generate a unique audit ID"""
    return f"aud_{uuid.uuid4().hex[:12]}"

def audit_event(
    event_type: str,
    entity_id: str,
    entity_type: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    """
    Log an audit event with complete explainability
    
    Args:
        event_type: Type of event (e.g., "leak_detected", "action_created", "action_executed")
        entity_id: ID of the entity involved (lead_id or action_id)
        entity_type: Type of entity (e.g., "lead", "action")
        details: Additional details about the event containing:
            For leak_detected:
                - what_detected: str (description of the leak)
                - why_detected: str (explanation)
                - rule_id: str
                - rule_name: str
                - severity: str
                - evidence: dict
                - recommended_recovery: str
            For action_created:
                - action_type: str
                - description: str
                - priority: int
                - reason: str
            For action_executed:
                - action_type: str
                - execution_notes: str
                - outcome: str
    
    Returns:
        audit_id: Unique identifier for the audit entry
    """
    audit_id = generate_audit_id()
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    audit_entry = {
        "audit_id": audit_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "entity_id": entity_id,
        "entity_type": entity_type,
        "details": details if details else {}
    }
    
    # Store audit entry
    audit_trail_db[audit_id] = audit_entry
    
    return audit_id

def get_audit_trail(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get recent audit entries
    
    Args:
        limit: Maximum number of entries to return (default 100)
        
    Returns:
        List of audit entries sorted by timestamp (most recent first)
    """
    # Get all audit entries
    all_entries = list(audit_trail_db.values())
    
    # Sort by timestamp (most recent first)
    all_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Return limited results
    return all_entries[:limit]

def get_audit_by_entity(entity_id: str) -> List[Dict[str, Any]]:
    """
    Get audit trail for a specific entity
    
    Args:
        entity_id: ID of the entity (lead_id or action_id)
        
    Returns:
        List of audit entries for the entity sorted by timestamp (most recent first)
    """
    # Filter entries by entity_id
    entity_entries = [
        entry for entry in audit_trail_db.values()
        if entry["entity_id"] == entity_id
    ]
    
    # Sort by timestamp (most recent first)
    entity_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return entity_entries

def get_audit_by_type(event_type: str) -> List[Dict[str, Any]]:
    """
    Get audit entries by event type
    
    Args:
        event_type: Type of event to filter by
        
    Returns:
        List of audit entries of the specified type sorted by timestamp (most recent first)
    """
    # Filter entries by event_type
    type_entries = [
        entry for entry in audit_trail_db.values()
        if entry["event_type"] == event_type
    ]
    
    # Sort by timestamp (most recent first)
    type_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return type_entries

def clear_audit_logs() -> None:
    """
    Clear all audit logs
    
    This is used for testing and maintenance purposes.
    """
    audit_trail_db.clear()

# Made with Bob
