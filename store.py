from typing import Dict, List, Optional
from datetime import datetime
import uuid

# ============================================================================
# IN-MEMORY DATA STORAGE
# ============================================================================

leads_db: Dict[str, dict] = {}
workflow_steps_db: Dict[str, List[dict]] = {}
recovery_actions_db: Dict[str, dict] = {}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())[:8]

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat() + "Z"

def calculate_time_since(timestamp: str) -> float:
    """Calculate hours since a timestamp"""
    try:
        created = datetime.fromisoformat(timestamp.replace("Z", ""))
        now = datetime.utcnow()
        delta = now - created
        return delta.total_seconds() / 3600  # Convert to hours
    except:
        return 0

# ============================================================================
# DATA ACCESS FUNCTIONS
# ============================================================================

def get_lead(lead_id: str) -> Optional[dict]:
    """Get a lead by ID"""
    return leads_db.get(lead_id)

def save_lead(lead_id: str, lead_data: dict) -> None:
    """Save a lead to the database"""
    leads_db[lead_id] = lead_data

def get_workflow_steps(lead_id: str) -> List[dict]:
    """Get workflow steps for a lead"""
    return workflow_steps_db.get(lead_id, [])

def add_workflow_step(lead_id: str, step_data: dict) -> None:
    """Add a workflow step for a lead"""
    if lead_id not in workflow_steps_db:
        workflow_steps_db[lead_id] = []
    workflow_steps_db[lead_id].append(step_data)

def get_all_leads() -> Dict[str, dict]:
    """Get all leads"""
    return leads_db

def clear_all_data() -> None:
    """Clear all data from storage"""
    leads_db.clear()
    workflow_steps_db.clear()
    recovery_actions_db.clear()

# ============================================================================
# RECOVERY ACTION FUNCTIONS
# ============================================================================

def save_recovery_action(action: dict) -> None:
    """Save a recovery action to the database"""
    recovery_actions_db[action["action_id"]] = action

def get_recovery_action(action_id: str) -> Optional[dict]:
    """Get a recovery action by ID"""
    return recovery_actions_db.get(action_id)

def get_all_recovery_actions() -> Dict[str, dict]:
    """Get all recovery actions"""
    return recovery_actions_db

def get_pending_actions() -> List[dict]:
    """Get all pending recovery actions"""
    return [action for action in recovery_actions_db.values() if action.get("status") == "pending"]

def get_executed_actions() -> List[dict]:
    """Get all executed recovery actions"""
    return [action for action in recovery_actions_db.values() if action.get("status") == "executed"]

def update_action_status(action_id: str, status: str, notes: Optional[str] = None) -> bool:
    """
    Update the status of a recovery action
    
    Args:
        action_id: ID of the action to update
        status: New status ("pending", "executed", "failed")
        notes: Optional execution notes
        
    Returns:
        True if update was successful, False if action not found
    """
    if action_id not in recovery_actions_db:
        return False
    
    recovery_actions_db[action_id]["status"] = status
    
    if status == "executed":
        recovery_actions_db[action_id]["executed_at"] = get_current_timestamp()
    
    if notes:
        recovery_actions_db[action_id]["execution_notes"] = notes
    
    return True

# Made with Bob
