from typing import List
from models import RecoveryAction, LeakDetection, LeakType
from store import generate_id, get_current_timestamp, save_recovery_action, get_all_recovery_actions
from events import log_event, EventType
from audit import audit_event

# ============================================================================
# RECOVERY ACTION GENERATION
# ============================================================================

def generate_recovery_actions(leaks: List[LeakDetection]) -> List[RecoveryAction]:
    """
    Generate recovery actions based on detected leaks
    BUG FIX 6: Prevent duplicate recovery actions for same leak_id/action_type
    
    Args:
        leaks: List of detected leaks
        
    Returns:
        List of recovery actions sorted by priority
    """
    recovery_actions = []
    
    # BUG FIX 6: Get existing actions to check for duplicates
    existing_actions = get_all_recovery_actions()
    existing_keys = set()
    for action in existing_actions.values():
        # Create unique key from leak_id and action_type
        key = f"{action.get('leak_id', '')}:{action.get('action_type', '')}"
        existing_keys.add(key)
    
    for leak in leaks:
        action = _create_recovery_action_for_leak(leak)
        if action:
            # BUG FIX 6: Check if action already exists for this leak_id/action_type
            action_key = f"{leak.leak_id}:{action.action_type}"
            if action_key in existing_keys:
                # Skip duplicate action, but add to return list if it exists
                for existing_action in existing_actions.values():
                    if (existing_action.get('leak_id') == leak.leak_id and
                        existing_action.get('action_type') == action.action_type):
                        # Return existing action as RecoveryAction object
                        recovery_actions.append(RecoveryAction(**existing_action))
                        break
                continue
            
            # Convert action to dict and save to store
            action_dict = action.model_dump()
            save_recovery_action(action_dict)
            existing_keys.add(action_key)  # Track this new action
            
            recovery_actions.append(action)
            
            # Log recovery action creation event
            log_event(
                EventType.RECOVERY_ACTION_CREATED,
                leak.lead_id,
                {
                    "action_type": action.action_type,
                    "lead_id": leak.lead_id,
                    "priority": action.priority,
                    "status": action.status
                }
            )
            
            # Audit trail for action creation
            audit_event(
                event_type="action_created",
                entity_id=action.action_id,
                entity_type="action",
                details={
                    "action_type": action.action_type,
                    "description": action.description,
                    "priority": action.priority,
                    "reason": f"Created to address {leak.type.value} leak for lead {leak.lead_name}"
                }
            )
    
    # Sort recovery actions by priority (lower number = higher priority)
    recovery_actions.sort(key=lambda x: x.priority)
    
    return recovery_actions

def _create_recovery_action_for_leak(leak: LeakDetection) -> RecoveryAction:
    """
    Create a recovery action for a specific leak
    
    Args:
        leak: The detected leak
        
    Returns:
        A recovery action tailored to the leak type
    """
    timestamp = get_current_timestamp()
    
    if leak.type == LeakType.MISSING_OWNER:
        return RecoveryAction(
            action_id=generate_id(),
            leak_id=leak.leak_id,
            action_type="assign_owner",
            description=f"Assign owner to lead '{leak.lead_name}'",
            priority=2,
            status="pending",
            created_at=timestamp,
            executed_at=None,
            execution_notes=None,
            recommendation=leak.recommendation
        )
    
    elif leak.type == LeakType.CLIENT_WAITING:
        return RecoveryAction(
            action_id=generate_id(),
            leak_id=leak.leak_id,
            action_type="urgent_response",
            description=f"URGENT: Respond to lead '{leak.lead_name}' immediately",
            priority=1,
            status="pending",
            created_at=timestamp,
            executed_at=None,
            execution_notes=None,
            recommendation=leak.recommendation
        )
    
    elif leak.type == LeakType.MISSING_FOLLOWUP:
        return RecoveryAction(
            action_id=generate_id(),
            leak_id=leak.leak_id,
            action_type="schedule_followup",
            description=f"Schedule follow-up for lead '{leak.lead_name}'",
            priority=2,
            status="pending",
            created_at=timestamp,
            executed_at=None,
            execution_notes=None,
            recommendation=leak.recommendation
        )
    
    elif leak.type == LeakType.STALE_LEAD:
        return RecoveryAction(
            action_id=generate_id(),
            leak_id=leak.leak_id,
            action_type="reactivate_lead",
            description=f"Review stale lead '{leak.lead_name}'",
            priority=3,
            status="pending",
            created_at=timestamp,
            executed_at=None,
            execution_notes=None,
            recommendation=leak.recommendation
        )
    
    # Default action if leak type is unknown
    return RecoveryAction(
        action_id=generate_id(),
        leak_id=leak.leak_id,
        action_type="review_lead",
        description=f"Review lead '{leak.lead_name}'",
        priority=3,
        status="pending",
        created_at=timestamp,
        executed_at=None,
        execution_notes=None,
        recommendation=leak.recommendation
    )

# Made with Bob
