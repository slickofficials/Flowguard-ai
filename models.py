from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    WAITING = "waiting"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    WON = "closed_won"  # Alias for CLOSED_WON
    LOST = "closed_lost"  # Alias for CLOSED_LOST

class LeakSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class LeakType(str, Enum):
    MISSING_OWNER = "missing_owner"
    MISSING_FOLLOWUP = "missing_followup"
    CLIENT_WAITING = "client_waiting"
    STALE_LEAD = "stale_lead"
    REPEATED_STATUS = "repeated_status"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LeadCreate(BaseModel):
    name: str = Field(..., description="Lead name (required)")
    message: str = Field(..., description="Lead message (required)")
    owner: Optional[str] = Field(None, description="Lead owner (optional)")

class LeadResponse(BaseModel):
    id: str
    name: str
    message: str
    owner: str
    status: LeadStatus
    created_at: str
    last_updated: str
    workflow_steps: List[str]

class WorkflowStepUpdate(BaseModel):
    lead_id: str = Field(..., description="Lead ID")
    step: str = Field(..., description="Workflow step description")
    status: Optional[LeadStatus] = Field(None, description="New status for the lead")

class LeakDetection(BaseModel):
    leak_id: str
    type: LeakType
    lead_id: str
    lead_name: str
    severity: LeakSeverity
    description: str
    detected_at: str
    rule_id: str
    rule_name: str
    explanation: str
    evidence: Dict
    recommendation: str
    risk_score: int = 0  # 1-100 risk score
    estimated_revenue_risk: str = "low"  # "low", "medium", "high"
    urgency: str = "low"  # "low", "medium", "high", "immediate"

class RecoveryAction(BaseModel):
    action_id: str
    leak_id: str
    action_type: str
    description: str
    priority: int
    status: str  # "pending", "executed", "failed"
    created_at: str  # ISO 8601 timestamp
    executed_at: Optional[str] = None  # ISO 8601 timestamp, None if not executed
    execution_notes: Optional[str] = None  # notes from execution
    recommendation: Optional[str] = None  # recommendation text

class StatusResponse(BaseModel):
    total_leads: int
    workflow_state: List[LeadResponse]
    summary: Dict[str, int]

class LeaksResponse(BaseModel):
    total_leaks: int
    critical_count: int
    detected_leaks: List[LeakDetection]
    recovery_actions: List[RecoveryAction]

# Made with Bob
