from typing import Dict, List
from models import LeakDetection, LeakSeverity, LeadStatus
from store import get_all_leads, get_all_recovery_actions, calculate_time_since

# ============================================================================
# BUSINESS IMPACT CALCULATION FUNCTIONS
# ============================================================================

def calculate_risk_score(leak: LeakDetection) -> int:
    """
    Calculate risk score (1-100) based on leak severity and additional factors
    
    Base scores by severity:
    - CRITICAL: 90-100
    - HIGH: 70-89
    - MEDIUM: 40-69
    - LOW: 1-39
    
    Additional factors:
    - Lead age (older = higher risk)
    - Status (qualified/negotiating = higher risk)
    - Evidence details
    
    Args:
        leak: LeakDetection object
        
    Returns:
        Risk score between 1 and 100
    """
    # Base score by severity
    base_scores = {
        LeakSeverity.CRITICAL: 95,
        LeakSeverity.HIGH: 80,
        LeakSeverity.MEDIUM: 55,
        LeakSeverity.LOW: 25
    }
    
    score = base_scores.get(leak.severity, 50)
    
    # Adjust based on evidence
    evidence = leak.evidence
    
    # Factor 1: Lead age (older leads = higher risk)
    if "lead_age_hours" in evidence:
        age_hours = evidence["lead_age_hours"]
        if age_hours > 72:
            score += 5
        elif age_hours > 48:
            score += 3
        elif age_hours > 24:
            score += 2
    
    if "hours_since_update" in evidence:
        hours_since = evidence["hours_since_update"]
        if hours_since > 48:
            score += 5
        elif hours_since > 36:
            score += 3
        elif hours_since > 24:
            score += 2
    
    # Factor 2: Repeated status (systematic issue)
    if "consecutive_count" in evidence:
        count = evidence["consecutive_count"]
        if count >= 5:
            score += 5
        elif count >= 4:
            score += 3
        elif count >= 3:
            score += 2
    
    # Ensure score stays within bounds
    return min(100, max(1, score))


def estimate_revenue_risk(leak: LeakDetection, lead: dict) -> str:
    """
    Estimate revenue risk based on leak severity and lead status
    
    Returns:
    - "high": CRITICAL leaks or HIGH leaks with qualified/negotiating status
    - "medium": HIGH leaks with other status or MEDIUM leaks with qualified status
    - "low": all other cases
    
    Args:
        leak: LeakDetection object
        lead: Lead data dictionary
        
    Returns:
        Revenue risk label: "low", "medium", or "high"
    """
    severity = leak.severity
    status = lead.get("status")
    
    # CRITICAL leaks always have high revenue risk
    if severity == LeakSeverity.CRITICAL:
        return "high"
    
    # HIGH severity leaks
    if severity == LeakSeverity.HIGH:
        # High revenue risk if lead is qualified or negotiating
        if status in [LeadStatus.QUALIFIED, LeadStatus.NEGOTIATING]:
            return "high"
        else:
            return "medium"
    
    # MEDIUM severity leaks
    if severity == LeakSeverity.MEDIUM:
        # Medium revenue risk if lead is qualified
        if status == LeadStatus.QUALIFIED:
            return "medium"
        else:
            return "low"
    
    # LOW severity leaks always have low revenue risk
    return "low"


def calculate_urgency(leak: LeakDetection, lead: dict) -> str:
    """
    Calculate urgency level based on leak type and severity
    
    Returns:
    - "immediate": CRITICAL severity or client_waiting type
    - "high": HIGH severity
    - "medium": MEDIUM severity
    - "low": LOW severity
    
    Args:
        leak: LeakDetection object
        lead: Lead data dictionary
        
    Returns:
        Urgency label: "low", "medium", "high", or "immediate"
    """
    severity = leak.severity
    leak_type = leak.type
    
    # Client waiting always requires immediate action
    if leak_type.value == "client_waiting":
        return "immediate"
    
    # Map severity to urgency
    if severity == LeakSeverity.CRITICAL:
        return "immediate"
    elif severity == LeakSeverity.HIGH:
        return "high"
    elif severity == LeakSeverity.MEDIUM:
        return "medium"
    else:
        return "low"


def get_business_impact_summary() -> Dict:
    """
    Get comprehensive business impact summary
    
    Returns:
        Dictionary containing:
        - total_leads: int
        - total_leaks: int
        - critical_leaks: int
        - high_leaks: int
        - medium_leaks: int
        - low_leaks: int
        - pending_actions: int
        - executed_actions: int
        - average_risk_score: float
        - total_high_revenue_risk: int
        - top_risk_leads: list of top 5 leads by risk score
    """
    from rules import detect_leaks  # Import here to avoid circular dependency
    
    leads_db = get_all_leads()
    leaks = detect_leaks()
    actions = get_all_recovery_actions()
    
    # Count leaks by severity
    critical_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.CRITICAL)
    high_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.HIGH)
    medium_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.MEDIUM)
    low_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.LOW)
    
    # Count actions by status
    pending_count = sum(1 for action in actions.values() if action.get("status") == "pending")
    executed_count = sum(1 for action in actions.values() if action.get("status") == "executed")
    
    # Calculate average risk score
    if leaks:
        total_risk = sum(calculate_risk_score(leak) for leak in leaks)
        avg_risk = round(total_risk / len(leaks), 2)
    else:
        avg_risk = 0.0
    
    # Count high revenue risk leaks
    high_revenue_risk_count = 0
    for leak in leaks:
        lead = leads_db.get(leak.lead_id)
        if lead and estimate_revenue_risk(leak, lead) == "high":
            high_revenue_risk_count += 1
    
    # Get top 5 risk leads
    leak_risk_data = []
    for leak in leaks:
        lead = leads_db.get(leak.lead_id)
        if lead:
            risk_score = calculate_risk_score(leak)
            revenue_risk = estimate_revenue_risk(leak, lead)
            urgency = calculate_urgency(leak, lead)
            
            leak_risk_data.append({
                "lead_id": leak.lead_id,
                "lead_name": leak.lead_name,
                "risk_score": risk_score,
                "severity": leak.severity.value,
                "revenue_risk": revenue_risk,
                "urgency": urgency,
                "leak_type": leak.type.value,
                "owner": lead.get("owner", "Unknown")
            })
    
    # Sort by risk score descending and take top 5
    top_risk_leads = sorted(leak_risk_data, key=lambda x: x["risk_score"], reverse=True)[:5]
    
    return {
        "total_leads": len(leads_db),
        "total_leaks": len(leaks),
        "critical_leaks": critical_count,
        "high_leaks": high_count,
        "medium_leaks": medium_count,
        "low_leaks": low_count,
        "pending_actions": pending_count,
        "executed_actions": executed_count,
        "average_risk_score": avg_risk,
        "total_high_revenue_risk": high_revenue_risk_count,
        "top_risk_leads": top_risk_leads
    }

# Made with Bob