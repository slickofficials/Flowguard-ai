from typing import List
from models import LeakDetection, LeakType, LeakSeverity, LeadStatus
from store import generate_id, get_current_timestamp, calculate_time_since, get_all_leads, get_workflow_steps
from events import log_event, EventType
from audit import audit_event
from impact import calculate_risk_score, estimate_revenue_risk, calculate_urgency

# ============================================================================
# LEAK DETECTION RULES
# ============================================================================

def detect_leaks() -> List[LeakDetection]:
    """
    Detect workflow leaks across all leads
    
    Applies 5 detection rules:
    1. Missing owner → HIGH severity (RULE_001)
    2. Client waiting (message or status) → CRITICAL severity (RULE_002)
    3. No follow-up for 24h+ → MEDIUM severity (RULE_003)
    4. Lead still NEW for 72h+ → LOW severity (RULE_004)
    5. Repeated stalled status → HIGH severity (RULE_005)
    
    Returns:
        List of detected leaks with enhanced metadata
    """
    leaks = []
    leads_db = get_all_leads()
    
    for lead_id, lead in leads_db.items():
        detected_leak_types = set()  # Track which leak types we've already detected for this lead
        
        # Rule 1: Missing owner → HIGH severity (RULE_001)
        if not lead.get("owner") or lead["owner"] == "Auto-assigned Agent":
            leak_id = generate_id()
            hours_since_creation = calculate_time_since(lead["created_at"])
            leak = LeakDetection(
                leak_id=leak_id,
                type=LeakType.MISSING_OWNER,
                lead_id=lead_id,
                lead_name=lead["name"],
                severity=LeakSeverity.HIGH,
                description=f"Lead '{lead['name']}' has no owner assigned",
                detected_at=get_current_timestamp(),
                rule_id="RULE_001",
                rule_name="Missing Owner Detection",
                explanation="Lead has no assigned owner, risking delayed response and lost opportunity",
                evidence={
                    "owner": lead.get("owner", "None"),
                    "lead_age_hours": round(hours_since_creation, 2)
                },
                recommendation="Assign to available sales representative immediately"
            )
            # Calculate business impact scores
            leak.risk_score = calculate_risk_score(leak)
            leak.estimated_revenue_risk = estimate_revenue_risk(leak, lead)
            leak.urgency = calculate_urgency(leak, lead)
            leaks.append(leak)
            detected_leak_types.add(LeakType.MISSING_OWNER)
            
            # Log leak detection event
            log_event(
                EventType.LEAK_DETECTED,
                lead_id,
                {
                    "leak_type": LeakType.MISSING_OWNER.value,
                    "severity": LeakSeverity.HIGH.value,
                    "lead_id": lead_id
                }
            )
            
            # Audit trail for leak detection
            audit_event(
                event_type="leak_detected",
                entity_id=lead_id,
                entity_type="lead",
                details={
                    "what_detected": leak.description,
                    "why_detected": leak.explanation,
                    "rule_id": leak.rule_id,
                    "rule_name": leak.rule_name,
                    "severity": leak.severity.value,
                    "evidence": leak.evidence,
                    "recommended_recovery": leak.recommendation
                }
            )
        
        # Rule 2: Message contains "waiting" OR status indicates waiting → CRITICAL (RULE_002)
        message_has_waiting = "waiting" in lead.get("message", "").lower()
        status_is_waiting = lead["status"] == LeadStatus.WAITING
        
        if (message_has_waiting or status_is_waiting) and LeakType.CLIENT_WAITING not in detected_leak_types:
            leak_id = generate_id()
            last_update_hours = calculate_time_since(lead["last_updated"])
            leak = LeakDetection(
                leak_id=leak_id,
                type=LeakType.CLIENT_WAITING,
                lead_id=lead_id,
                lead_name=lead["name"],
                severity=LeakSeverity.CRITICAL,
                description=f"Lead '{lead['name']}' is waiting - immediate action required",
                detected_at=get_current_timestamp(),
                rule_id="RULE_002",
                rule_name="Client Waiting Detection",
                explanation="Client explicitly indicated they are waiting for response, indicating high urgency",
                evidence={
                    "status": lead["status"],
                    "message_contains": "waiting" if message_has_waiting else "N/A",
                    "last_update_hours": round(last_update_hours, 2)
                },
                recommendation="Respond to client within 1 hour to prevent escalation"
            )
            # Calculate business impact scores
            leak.risk_score = calculate_risk_score(leak)
            leak.estimated_revenue_risk = estimate_revenue_risk(leak, lead)
            leak.urgency = calculate_urgency(leak, lead)
            leaks.append(leak)
            detected_leak_types.add(LeakType.CLIENT_WAITING)
            
            # Log leak detection event
            log_event(
                EventType.LEAK_DETECTED,
                lead_id,
                {
                    "leak_type": LeakType.CLIENT_WAITING.value,
                    "severity": LeakSeverity.CRITICAL.value,
                    "lead_id": lead_id
                }
            )
            
            # Audit trail for leak detection
            audit_event(
                event_type="leak_detected",
                entity_id=lead_id,
                entity_type="lead",
                details={
                    "what_detected": leak.description,
                    "why_detected": leak.explanation,
                    "rule_id": leak.rule_id,
                    "rule_name": leak.rule_name,
                    "severity": leak.severity.value,
                    "evidence": leak.evidence,
                    "recommended_recovery": leak.recommendation
                }
            )
        
        # Rule 3: No follow-up activity for 24h+ → MEDIUM (RULE_003)
        hours_since_update = calculate_time_since(lead["last_updated"])
        
        if hours_since_update > 24 and lead["status"] not in [LeadStatus.CLOSED_WON, LeadStatus.CLOSED_LOST] and LeakType.MISSING_FOLLOWUP not in detected_leak_types:
            leak_id = generate_id()
            workflow_steps = get_workflow_steps(lead_id)
            last_step = workflow_steps[-1]["step"] if workflow_steps else "None"
            leak = LeakDetection(
                leak_id=leak_id,
                type=LeakType.MISSING_FOLLOWUP,
                lead_id=lead_id,
                lead_name=lead["name"],
                severity=LeakSeverity.MEDIUM,
                description=f"Lead '{lead['name']}' has no follow-up for {int(hours_since_update)} hours",
                detected_at=get_current_timestamp(),
                rule_id="RULE_003",
                rule_name="Stale Workflow Detection",
                explanation="No workflow activity for 24+ hours on active lead, indicating process breakdown",
                evidence={
                    "hours_since_update": round(hours_since_update, 2),
                    "current_status": lead["status"],
                    "last_step": last_step
                },
                recommendation="Schedule immediate follow-up call or email"
            )
            # Calculate business impact scores
            leak.risk_score = calculate_risk_score(leak)
            leak.estimated_revenue_risk = estimate_revenue_risk(leak, lead)
            leak.urgency = calculate_urgency(leak, lead)
            leaks.append(leak)
            detected_leak_types.add(LeakType.MISSING_FOLLOWUP)
            
            # Log leak detection event
            log_event(
                EventType.LEAK_DETECTED,
                lead_id,
                {
                    "leak_type": LeakType.MISSING_FOLLOWUP.value,
                    "severity": LeakSeverity.MEDIUM.value,
                    "lead_id": lead_id
                }
            )
            
            # Audit trail for leak detection
            audit_event(
                event_type="leak_detected",
                entity_id=lead_id,
                entity_type="lead",
                details={
                    "what_detected": leak.description,
                    "why_detected": leak.explanation,
                    "rule_id": leak.rule_id,
                    "rule_name": leak.rule_name,
                    "severity": leak.severity.value,
                    "evidence": leak.evidence,
                    "recommended_recovery": leak.recommendation
                }
            )
        
        # Rule 4: Lead still in NEW for 72h+ → LOW (RULE_004)
        hours_since_creation = calculate_time_since(lead["created_at"])
        if hours_since_creation > 72 and lead["status"] == LeadStatus.NEW and LeakType.STALE_LEAD not in detected_leak_types:
            leak_id = generate_id()
            leak = LeakDetection(
                leak_id=leak_id,
                type=LeakType.STALE_LEAD,
                lead_id=lead_id,
                lead_name=lead["name"],
                severity=LeakSeverity.LOW,
                description=f"Lead '{lead['name']}' is stale ({int(hours_since_creation)} hours old, still NEW)",
                detected_at=get_current_timestamp(),
                rule_id="RULE_004",
                rule_name="New Lead Aging Detection",
                explanation="Lead remained in NEW status for 72+ hours without initial contact",
                evidence={
                    "hours_in_new_status": round(hours_since_creation, 2),
                    "created_at": lead["created_at"]
                },
                recommendation="Initiate first contact within 4 hours or reassign"
            )
            # Calculate business impact scores
            leak.risk_score = calculate_risk_score(leak)
            leak.estimated_revenue_risk = estimate_revenue_risk(leak, lead)
            leak.urgency = calculate_urgency(leak, lead)
            leaks.append(leak)
            detected_leak_types.add(LeakType.STALE_LEAD)
            
            # Log leak detection event
            log_event(
                EventType.LEAK_DETECTED,
                lead_id,
                {
                    "leak_type": LeakType.STALE_LEAD.value,
                    "severity": LeakSeverity.LOW.value,
                    "lead_id": lead_id
                }
            )
            
            # Audit trail for leak detection
            audit_event(
                event_type="leak_detected",
                entity_id=lead_id,
                entity_type="lead",
                details={
                    "what_detected": leak.description,
                    "why_detected": leak.explanation,
                    "rule_id": leak.rule_id,
                    "rule_name": leak.rule_name,
                    "severity": leak.severity.value,
                    "evidence": leak.evidence,
                    "recommended_recovery": leak.recommendation
                }
            )
        
        # Rule 5: Repeated stalled status across workflow steps → HIGH (RULE_005)
        workflow_steps = get_workflow_steps(lead_id)
        if len(workflow_steps) >= 3 and LeakType.REPEATED_STATUS not in detected_leak_types:
            # Check for repeated status in consecutive workflow steps
            status_counts = {}
            consecutive_status = []
            current_status = lead["status"]
            
            # Count how many times the current status appears in recent workflow steps
            for step_data in workflow_steps[-5:]:  # Check last 5 steps
                step = step_data["step"]
                if current_status in step.lower():
                    consecutive_status.append(step)
            
            # If status appears in 3+ consecutive steps, it's a repeated stall
            if len(consecutive_status) >= 3:
                leak_id = generate_id()
                leak = LeakDetection(
                    leak_id=leak_id,
                    type=LeakType.REPEATED_STATUS,
                    lead_id=lead_id,
                    lead_name=lead["name"],
                    severity=LeakSeverity.HIGH,
                    description=f"Lead '{lead['name']}' shows repeated stalled status across {len(consecutive_status)} workflow steps",
                    detected_at=get_current_timestamp(),
                    rule_id="RULE_005",
                    rule_name="Repeated Status Detection",
                    explanation="Lead shows repeated stalled status across multiple workflow steps, indicating systematic issue",
                    evidence={
                        "status": current_status,
                        "consecutive_count": len(consecutive_status),
                        "steps": consecutive_status
                    },
                    recommendation="Escalate to manager for process review"
                )
                # Calculate business impact scores
                leak.risk_score = calculate_risk_score(leak)
                leak.estimated_revenue_risk = estimate_revenue_risk(leak, lead)
                leak.urgency = calculate_urgency(leak, lead)
                leaks.append(leak)
                detected_leak_types.add(LeakType.REPEATED_STATUS)
                
                # Log leak detection event
                log_event(
                    EventType.LEAK_DETECTED,
                    lead_id,
                    {
                        "leak_type": LeakType.REPEATED_STATUS.value,
                        "severity": LeakSeverity.HIGH.value,
                        "lead_id": lead_id
                    }
                )
                
                # Audit trail for leak detection
                audit_event(
                    event_type="leak_detected",
                    entity_id=lead_id,
                    entity_type="lead",
                    details={
                        "what_detected": leak.description,
                        "why_detected": leak.explanation,
                        "rule_id": leak.rule_id,
                        "rule_name": leak.rule_name,
                        "severity": leak.severity.value,
                        "evidence": leak.evidence,
                        "recommended_recovery": leak.recommendation
                    }
                )
    
    return leaks

# Made with Bob
