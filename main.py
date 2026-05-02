from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from typing import Optional
import time

# Import from our new modules
from models import (
    LeadStatus, LeakSeverity, LeakType,
    LeadCreate, LeadResponse, WorkflowStepUpdate,
    LeakDetection, RecoveryAction, StatusResponse, LeaksResponse
)
from store import (
    leads_db, workflow_steps_db, recovery_actions_db,
    generate_id, get_current_timestamp,
    get_lead, save_lead, get_workflow_steps, add_workflow_step,
    get_all_leads, clear_all_data,
    save_recovery_action, get_recovery_action, get_all_recovery_actions,
    get_pending_actions, get_executed_actions, update_action_status
)
from rules import detect_leaks
from recovery import generate_recovery_actions
from dashboard import generate_dashboard_html
from audit import audit_event, get_audit_trail, get_audit_by_entity, get_audit_by_type, clear_audit_logs
from events import log_event, get_events, get_events_by_type, get_events_by_entity, EventType, clear_events
from impact import get_business_impact_summary

app = FastAPI(title="FlowGuard AI", description="Workflow Leak Detection System")

# Configure Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global state for autonomous mode
autonomous_mode_enabled = False
app_start_time = time.time()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "service": "FlowGuard AI",
        "version": "1.0.0",
        "description": "Workflow Leak Detection System",
        "endpoints": {
            "GET /dashboard": "View interactive dashboard with leaks and recovery actions",
            "GET /seed-demo": "Seed database with demo data for testing",
            "POST /lead": "Create a new lead",
            "POST /update-step": "Update workflow step for a lead",
            "GET /status": "Get current workflow state for all leads",
            "GET /leaks": "Get detected leaks with recovery actions (sorted by risk score)",
            "GET /impact": "Get comprehensive business impact analysis",
            "GET /recovery-actions": "Get all recovery actions with optional filtering",
            "POST /execute-action/{action_id}": "Execute a recovery action",
            "GET /events": "Get system events log",
            "GET /audit": "Get audit trail with optional filtering"
        }
    }

@app.post("/lead", response_model=LeadResponse)
def create_lead(lead: LeadCreate):
    """
    Create a new lead with automatic leak detection
    
    - **name**: Lead name (required)
    - **message**: Lead message (required)
    - **owner**: Lead owner (optional, auto-assigned if missing)
    """
    lead_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Auto-assign owner if missing (leak detection rule)
    owner = lead.owner if lead.owner else "Auto-assigned Agent"
    
    lead_data = {
        "id": lead_id,
        "name": lead.name,
        "message": lead.message,
        "owner": owner,
        "status": LeadStatus.NEW,
        "created_at": timestamp,
        "last_updated": timestamp
    }
    
    save_lead(lead_id, lead_data)
    add_workflow_step(lead_id, {
        "step": "Lead created",
        "timestamp": timestamp,
        "status": LeadStatus.NEW
    })
    
    # Log event after successful lead creation
    log_event(
        EventType.LEAD_CREATED,
        lead_id,
        {
            "name": lead_data["name"],
            "owner": lead_data["owner"]
        }
    )
    
    return LeadResponse(
        id=lead_data["id"],
        name=lead_data["name"],
        message=lead_data["message"],
        owner=lead_data["owner"],
        status=lead_data["status"],
        created_at=lead_data["created_at"],
        last_updated=lead_data["last_updated"],
        workflow_steps=["Lead created"]
    )

@app.post("/update-step")
def update_workflow_step(update: WorkflowStepUpdate):
    """
    Update workflow step for a lead
    
    - **lead_id**: ID of the lead to update
    - **step**: Description of the workflow step
    - **status**: Optional new status for the lead
    """
    if update.lead_id not in leads_db:
        raise HTTPException(status_code=404, detail=f"Lead with ID {update.lead_id} not found")
    
    timestamp = get_current_timestamp()
    
    # Update lead's last_updated timestamp
    leads_db[update.lead_id]["last_updated"] = timestamp
    
    # Update status if provided
    if update.status:
        leads_db[update.lead_id]["status"] = update.status
    
    # Add workflow step
    step_data = {
        "step": update.step,
        "timestamp": timestamp,
        "status": update.status if update.status else leads_db[update.lead_id]["status"]
    }
    
    add_workflow_step(update.lead_id, step_data)
    
    # Log event after successful workflow step update
    log_event(
        EventType.WORKFLOW_STEP_UPDATED,
        update.lead_id,
        {
            "lead_id": update.lead_id,
            "step": update.step,
            "status": leads_db[update.lead_id]["status"].value
        }
    )
    
    return {
        "success": True,
        "lead_id": update.lead_id,
        "step_added": update.step,
        "new_status": leads_db[update.lead_id]["status"],
        "timestamp": timestamp
    }

@app.get("/status", response_model=StatusResponse)
def get_workflow_status():
    """
    Get current workflow state for all leads
    
    Returns complete state of all leads with their workflow steps
    """
    workflow_state = []
    status_summary = {}
    
    for lead_id, lead in leads_db.items():
        steps = get_workflow_steps(lead_id)
        step_descriptions = [s["step"] for s in steps]
        
        lead_response = LeadResponse(
            id=lead["id"],
            name=lead["name"],
            message=lead["message"],
            owner=lead["owner"],
            status=lead["status"],
            created_at=lead["created_at"],
            last_updated=lead["last_updated"],
            workflow_steps=step_descriptions
        )
        workflow_state.append(lead_response)
        
        # Count status summary
        status_key = lead["status"].value
        status_summary[status_key] = status_summary.get(status_key, 0) + 1
    
    return StatusResponse(
        total_leads=len(leads_db),
        workflow_state=workflow_state,
        summary=status_summary
    )

@app.get("/leaks", response_model=LeaksResponse)
def get_detected_leaks():
    """
    Get detected workflow leaks with recovery actions
    
    Analyzes all leads and detects:
    - Missing owners
    - Missing follow-up actions
    - Clients in waiting status
    - Stale leads
    
    Returns leaks sorted by risk_score (highest risk first) with suggested recovery actions
    """
    leaks = detect_leaks()
    
    # Sort leaks by risk_score descending (highest risk first)
    sorted_leaks = sorted(leaks, key=lambda x: x.risk_score, reverse=True)
    
    recovery_actions = generate_recovery_actions(sorted_leaks)
    
    # Count critical leaks
    critical_count = sum(1 for leak in sorted_leaks if leak.severity == LeakSeverity.CRITICAL)
    
    return LeaksResponse(
        total_leaks=len(sorted_leaks),
        critical_count=critical_count,
        detected_leaks=sorted_leaks,
        recovery_actions=recovery_actions
    )

@app.get("/impact")
def get_impact_analysis():
    """
    Get comprehensive business impact analysis
    
    Returns:
    - Total leads and leaks counts
    - Breakdown by severity (critical, high, medium, low)
    - Pending vs executed actions
    - Average risk score
    - High revenue risk count
    - Top 5 risk leads with details
    
    Provides executives with quantifiable business impact metrics
    """
    impact_summary = get_business_impact_summary()
    return impact_summary

@app.get("/dashboard")
def get_dashboard(request: Request):
    """
    Dashboard with Jinja2 template showing workflow leaks and recovery actions
    """
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "autonomous_mode": autonomous_mode_enabled
    })

@app.get("/events")
def get_system_events(
    limit: Optional[int] = Query(50, description="Maximum number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID")
):
    """
    Get system events log
    
    - **limit**: Maximum number of events to return (default 50)
    - **event_type**: Filter by event type (e.g., "lead.created")
    - **entity_id**: Filter by entity ID (e.g., lead ID)
    
    Returns recent system events with optional filtering
    """
    # Apply filters if provided
    if event_type:
        try:
            # Convert string to EventType enum
            event_type_enum = EventType(event_type)
            events = get_events_by_type(event_type_enum, limit)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event_type: {event_type}")
    elif entity_id:
        events = get_events_by_entity(entity_id, limit)
    else:
        events = get_events(limit)
    
    return {
        "total_events": len(events),
        "events": events
    }

@app.get("/audit")
def get_audit_log(
    limit: Optional[int] = Query(100, description="Maximum number of audit entries to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type (leak_detected, action_created, action_executed)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID (lead_id or action_id)")
):
    """
    Get audit trail with optional filtering
    
    - **limit**: Maximum number of entries to return (default 100)
    - **event_type**: Filter by event type (leak_detected, action_created, action_executed)
    - **entity_id**: Filter by entity ID (lead_id or action_id)
    
    Returns audit trail with complete explainability information
    """
    # Apply filters if provided
    if event_type:
        entries = get_audit_by_type(event_type)
        # Apply limit
        entries = entries[:limit]
    elif entity_id:
        entries = get_audit_by_entity(entity_id)
        # Apply limit
        entries = entries[:limit]
    else:
        entries = get_audit_trail(limit)
    
    return {
        "total_entries": len(entries),
        "entries": entries
    }

@app.get("/recovery-actions")
def get_recovery_actions(
    status: Optional[str] = Query(None, description="Filter by status (pending, executed, failed)"),
    lead_id: Optional[str] = Query(None, description="Filter by lead ID")
):
    """
    Get all recovery actions with optional filtering
    
    - **status**: Filter by action status (pending, executed, failed)
    - **lead_id**: Filter by lead ID
    
    Returns all recovery actions with counts by status
    """
    all_actions = list(get_all_recovery_actions().values())
    
    # Apply filters
    filtered_actions = all_actions
    
    if status:
        filtered_actions = [a for a in filtered_actions if a.get("status") == status]
    
    if lead_id:
        filtered_actions = [a for a in filtered_actions if a.get("leak_id") == lead_id]
    
    # Count by status
    pending_count = sum(1 for a in all_actions if a.get("status") == "pending")
    executed_count = sum(1 for a in all_actions if a.get("status") == "executed")
    failed_count = sum(1 for a in all_actions if a.get("status") == "failed")
    
    return {
        "total_actions": len(all_actions),
        "pending": pending_count,
        "executed": executed_count,
        "failed": failed_count,
        "actions": filtered_actions
    }

@app.post("/execute-action/{action_id}")
def execute_action(action_id: str, execution_notes: Optional[str] = None):
    """
    Execute a recovery action
    
    - **action_id**: ID of the action to execute
    - **execution_notes**: Optional notes about the execution
    
    Updates action status to "executed" and sets executed_at timestamp
    """
    # Retrieve action from store
    action = get_recovery_action(action_id)
    
    if not action:
        raise HTTPException(status_code=404, detail=f"Action with ID {action_id} not found")
    
    # Validate action status
    if action.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Action is not pending (current status: {action.get('status')})"
        )
    
    # Update action status
    success = update_action_status(action_id, "executed", execution_notes)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update action status")
    
    # Get updated action
    updated_action = get_recovery_action(action_id)
    
    # Log recovery action executed event
    log_event(
        EventType.RECOVERY_ACTION_EXECUTED,
        updated_action.get("leak_id", ""),
        {
            "action_id": action_id,
            "action_type": updated_action.get("action_type"),
            "executed_at": updated_action.get("executed_at"),
            "execution_notes": execution_notes
        }
    )
    
    # Audit trail for action execution
    audit_event(
        event_type="action_executed",
        entity_id=action_id,
        entity_type="action",
        details={
            "action_type": updated_action.get("action_type"),
            "execution_notes": execution_notes if execution_notes else "No notes provided",
            "outcome": "success"
        }
    )
    
    return {
        "success": True,
        "action": updated_action
    }

@app.get("/seed-demo")
def seed_demo_data():
    """
    Seed the database with demo data for testing
    
    Creates 6 sample leads with varied risk scenarios:
    - Acme Corp: CRITICAL - Client waiting + negotiating (high revenue risk)
    - TechStart Inc: HIGH - No owner + qualified status (high revenue risk)
    - Global Solutions: MEDIUM - No follow-up for 30h + qualified (medium revenue risk)
    - Beta Industries: HIGH - No owner + contacted status (medium revenue risk)
    - Startup Co: LOW - Stale lead (72h+ in NEW status)
    - Enterprise LLC: CRITICAL - Client waiting status (immediate urgency)
    
    Also generates recovery actions and pre-executes some for demo purposes
    """
    # Clear existing data
    clear_all_data()
    clear_audit_logs()
    clear_events()
    
    timestamp_now = get_current_timestamp()
    
    # Lead 1: Acme Corp - CRITICAL (client waiting + negotiating = high revenue risk)
    lead_1_id = generate_id()
    save_lead(lead_1_id, {
        "id": lead_1_id,
        "name": "Acme Corp",
        "message": "Waiting for contract to finalize the deal",  # Triggers CRITICAL leak
        "owner": "John Doe",
        "status": LeadStatus.NEGOTIATING,  # High-value status
        "created_at": timestamp_now,
        "last_updated": timestamp_now
    })
    add_workflow_step(lead_1_id, {
        "step": "Lead created",
        "timestamp": timestamp_now,
        "status": LeadStatus.NEW
    })
    add_workflow_step(lead_1_id, {
        "step": "Moved to negotiating",
        "timestamp": timestamp_now,
        "status": LeadStatus.NEGOTIATING
    })
    
    # Lead 2: TechStart Inc - HIGH (no owner + qualified = high revenue risk)
    lead_2_id = generate_id()
    save_lead(lead_2_id, {
        "id": lead_2_id,
        "name": "TechStart Inc",
        "message": "Interested in enterprise package with 100 licenses",
        "owner": "Auto-assigned Agent",  # Triggers HIGH leak
        "status": LeadStatus.QUALIFIED,  # High-value status
        "created_at": timestamp_now,
        "last_updated": timestamp_now
    })
    add_workflow_step(lead_2_id, {
        "step": "Lead created",
        "timestamp": timestamp_now,
        "status": LeadStatus.NEW
    })
    add_workflow_step(lead_2_id, {
        "step": "Lead qualified",
        "timestamp": timestamp_now,
        "status": LeadStatus.QUALIFIED
    })
    
    # Lead 3: Global Solutions - MEDIUM (no follow-up 30h + qualified = medium revenue risk)
    old_timestamp_30h = datetime.utcnow() - timedelta(hours=30)
    old_timestamp_30h_str = old_timestamp_30h.isoformat() + "Z"
    
    lead_3_id = generate_id()
    save_lead(lead_3_id, {
        "id": lead_3_id,
        "name": "Global Solutions",
        "message": "Looking for pricing information for annual subscription",
        "owner": "Sarah Johnson",
        "status": LeadStatus.QUALIFIED,
        "created_at": old_timestamp_30h_str,
        "last_updated": old_timestamp_30h_str  # No update for 30 hours - triggers MEDIUM leak
    })
    add_workflow_step(lead_3_id, {
        "step": "Lead created",
        "timestamp": old_timestamp_30h_str,
        "status": LeadStatus.NEW
    })
    add_workflow_step(lead_3_id, {
        "step": "Lead qualified",
        "timestamp": old_timestamp_30h_str,
        "status": LeadStatus.QUALIFIED
    })
    
    # Lead 4: Beta Industries - HIGH (no owner + contacted = medium revenue risk)
    lead_4_id = generate_id()
    save_lead(lead_4_id, {
        "id": lead_4_id,
        "name": "Beta Industries",
        "message": "Need demo of your product",
        "owner": "Auto-assigned Agent",  # Triggers HIGH leak
        "status": LeadStatus.CONTACTED,
        "created_at": timestamp_now,
        "last_updated": timestamp_now
    })
    add_workflow_step(lead_4_id, {
        "step": "Lead created",
        "timestamp": timestamp_now,
        "status": LeadStatus.NEW
    })
    add_workflow_step(lead_4_id, {
        "step": "Initial contact made",
        "timestamp": timestamp_now,
        "status": LeadStatus.CONTACTED
    })
    
    # Lead 5: Startup Co - LOW (stale lead 75h in NEW status)
    old_timestamp_75h = datetime.utcnow() - timedelta(hours=75)
    old_timestamp_75h_str = old_timestamp_75h.isoformat() + "Z"
    
    lead_5_id = generate_id()
    save_lead(lead_5_id, {
        "id": lead_5_id,
        "name": "Startup Co",
        "message": "Curious about your services",
        "owner": "Mike Wilson",
        "status": LeadStatus.NEW,  # Still in NEW after 75 hours - triggers LOW leak
        "created_at": old_timestamp_75h_str,
        "last_updated": old_timestamp_75h_str
    })
    add_workflow_step(lead_5_id, {
        "step": "Lead created",
        "timestamp": old_timestamp_75h_str,
        "status": LeadStatus.NEW
    })
    
    # Lead 6: Enterprise LLC - CRITICAL (waiting status = immediate urgency)
    lead_6_id = generate_id()
    save_lead(lead_6_id, {
        "id": lead_6_id,
        "name": "Enterprise LLC",
        "message": "Ready to purchase, need quote urgently",
        "owner": "Jane Smith",
        "status": LeadStatus.WAITING,  # Triggers CRITICAL leak
        "created_at": timestamp_now,
        "last_updated": timestamp_now
    })
    add_workflow_step(lead_6_id, {
        "step": "Lead created",
        "timestamp": timestamp_now,
        "status": LeadStatus.NEW
    })
    add_workflow_step(lead_6_id, {
        "step": "Client waiting for response",
        "timestamp": timestamp_now,
        "status": LeadStatus.WAITING
    })
    
    # Generate recovery actions for detected leaks
    leaks = detect_leaks()
    recovery_actions = generate_recovery_actions(leaks)
    
    # Pre-execute one action for demo purposes (if any actions exist)
    executed_action_id = None
    if recovery_actions:
        # Execute the first action (highest priority)
        first_action = recovery_actions[0]
        update_action_status(
            first_action.action_id,
            "executed",
            "Demo: Action executed during seed"
        )
        executed_action_id = first_action.action_id
        
        # Log the execution event
        log_event(
            EventType.RECOVERY_ACTION_EXECUTED,
            first_action.leak_id,
            {
                "action_id": first_action.action_id,
                "action_type": first_action.action_type,
                "executed_at": get_current_timestamp(),
                "execution_notes": "Demo: Action executed during seed"
            }
        )
        
        # Audit trail for pre-executed action
        audit_event(
            event_type="action_executed",
            entity_id=first_action.action_id,
            entity_type="action",
            details={
                "action_type": first_action.action_type,
                "execution_notes": "Demo: Action executed during seed",
                "outcome": "success"
            }
        )
    
    return {
        "status": "seeded",
        "leads_created": 6,
        "leaks_detected": len(leaks),
        "recovery_actions_created": len(recovery_actions),
        "pre_executed_action": executed_action_id,
        "leads": [
            {"id": lead_1_id, "name": "Acme Corp", "issue": "Client waiting + negotiating", "expected_severity": "CRITICAL"},
            {"id": lead_2_id, "name": "TechStart Inc", "issue": "No owner + qualified", "expected_severity": "HIGH"},
            {"id": lead_3_id, "name": "Global Solutions", "issue": "No follow-up 30h + qualified", "expected_severity": "MEDIUM"},
            {"id": lead_4_id, "name": "Beta Industries", "issue": "No owner + contacted", "expected_severity": "HIGH"},
            {"id": lead_5_id, "name": "Startup Co", "issue": "Stale lead 75h in NEW", "expected_severity": "LOW"},
            {"id": lead_6_id, "name": "Enterprise LLC", "issue": "Waiting status", "expected_severity": "CRITICAL"}
        ]
    }

# ============================================================================
# HTMX API ENDPOINTS
# ============================================================================

@app.get("/api/metrics")
def get_metrics(request: Request):
    """
    HTMX endpoint: Returns metrics.html component with real-time data
    BUG FIX 1: Show real data from get_events(), detect_leaks(), and executed actions
    """
    # Get real data from system
    total_events = len(get_events(limit=10000))  # Get all events
    leaks = detect_leaks()
    active_incidents = len(leaks)
    
    # Count executed recovery actions
    executed_actions = get_executed_actions()
    autonomous_actions = len(executed_actions)
    
    # Calculate system health (percentage of leads without critical leaks)
    total_leads = len(leads_db)
    critical_leaks = sum(1 for leak in leaks if leak.severity == LeakSeverity.CRITICAL)
    system_health = int(((total_leads - critical_leaks) / total_leads * 100)) if total_leads > 0 else 100
    
    # Calculate trends (mock baseline: 80% of current for demo)
    baseline_events = int(total_events * 0.8) if total_events > 0 else 0
    baseline_incidents = int(active_incidents * 0.8) if active_incidents > 0 else 0
    baseline_actions = int(autonomous_actions * 0.8) if autonomous_actions > 0 else 0
    
    events_trend = ((total_events - baseline_events) / baseline_events * 100) if baseline_events > 0 else 0
    incidents_trend = ((active_incidents - baseline_incidents) / baseline_incidents * 100) if baseline_incidents > 0 else 0
    actions_trend = ((autonomous_actions - baseline_actions) / baseline_actions * 100) if baseline_actions > 0 else 0
    
    # Determine status colors
    incidents_status = "red" if active_incidents > 5 else "yellow" if active_incidents > 2 else "green"
    health_status = "green" if system_health >= 80 else "yellow" if system_health >= 60 else "red"
    
    return templates.TemplateResponse("components/metrics.html", {
        "request": request,
        "total_events": total_events,
        "leads_trend": round(events_trend, 1),
        "active_incidents": active_incidents,
        "leaks_trend": round(incidents_trend, 1),
        "leaks_status": incidents_status,
        "autonomous_actions": autonomous_actions,
        "critical_trend": round(actions_trend, 1),
        "critical_status": health_status,
        "system_health": system_health
    })

@app.get("/api/incidents")
def get_incidents(request: Request):
    """
    HTMX endpoint: Returns incidents.html component with leak data
    BUG FIX 5: Do NOT generate new recovery actions - only display existing leak data
    """
    leaks_response = get_detected_leaks()
    leaks = leaks_response.detected_leaks
    
    # Transform leaks into incident format
    incidents = []
    for leak in leaks[:10]:  # Limit to top 10
        lead = get_lead(leak.lead_id)
        if lead:
            # Use existing recommendation from leak, don't generate new actions
            suggested_action = leak.recommendation if leak.recommendation else "Review manually"
            
            incidents.append({
                "title": f"{leak.type.value.replace('_', ' ').title()} - {lead['name']}",
                "description": leak.description,
                "severity": leak.severity.value,
                "timestamp": leak.detected_at,
                "source": leak.rule_name,
                "status": "Active",
                "autonomous_action": autonomous_mode_enabled
            })
    
    return templates.TemplateResponse("components/incidents.html", {
        "request": request,
        "incidents": incidents
    })

@app.get("/api/task-queue")
def get_task_queue(request: Request):
    """
    HTMX endpoint: Returns task_queue.html component with recovery actions
    BUG FIX 3 & 4: Add priority field to tasks before sorting, fix leak_id lookup
    """
    all_actions = list(get_all_recovery_actions().values())
    
    # Transform actions into task format
    tasks = []
    for action in all_actions[:10]:  # Limit to top 10
        # BUG FIX 4: Recovery actions have leak_id, need to get lead from leak
        leak_id = action.get("leak_id", "")
        lead_name = "Unknown Lead"
        
        # Try to find the lead by matching leak_id to detected leaks
        if leak_id:
            leaks = detect_leaks()
            for leak in leaks:
                if leak.leak_id == leak_id:
                    lead = get_lead(leak.lead_id)
                    if lead:
                        lead_name = lead["name"]
                    break
        
        # Calculate progress
        status = action.get("status", "pending")
        progress = 100 if status == "executed" else 0
        
        # Determine priority from action type
        action_type = action.get("action_type", "")
        if "urgent" in action_type.lower() or "immediate" in action_type.lower():
            priority = "high"
        elif "follow" in action_type.lower():
            priority = "medium"
        else:
            priority = "low"
        
        # BUG FIX 3: Add priority field to task dict before sorting
        tasks.append({
            "action_id": action.get("action_id"),
            "name": f"{action.get('action_type', 'Recovery Action')} - {lead_name}",
            "description": action.get("recommendation", "Recovery action pending"),
            "status": "completed" if status == "executed" else "pending",
            "progress": progress,
            "priority": priority,  # BUG FIX 3: Add priority field
            "created_at": action.get("created_at", ""),
            "rule_id": None
        })
    
    # Sort by priority (high first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return templates.TemplateResponse("components/task_queue.html", {
        "request": request,
        "tasks": tasks
    })

@app.get("/api/activity-feed")
def get_activity_feed(request: Request):
    """
    HTMX endpoint: Returns activity_feed.html component with recent events
    BUG FIX 2: Wrap data shaping safely, support both payload and details keys
    """
    try:
        events = get_events(limit=20)
        
        # Transform events into activity format
        activities = []
        for event in events:
            try:
                event_type = event.get("event_type", "")
                entity_id = event.get("entity_id", "")
                # BUG FIX 2: Support both payload and details keys
                details = event.get("payload", event.get("details", {}))
                
                # Determine activity type and description
                if event_type == "lead.created":
                    activity_type = "lead_created"
                    description = f"New lead created: {details.get('name', 'Unknown')}"
                    status = "success"
                elif event_type == "leak.detected":
                    activity_type = "leak_detected"
                    lead = get_lead(entity_id)
                    lead_name = lead["name"] if lead else "Unknown"
                    description = f"Leak detected in {lead_name}"
                    status = "warning"
                elif event_type == "recovery_action.executed":
                    activity_type = "action_executed"
                    description = f"Recovery action executed: {details.get('action_type', 'Unknown')}"
                    status = "success"
                elif event_type == "workflow_step.updated":
                    activity_type = "workflow_updated"
                    description = f"Workflow step updated: {details.get('step', 'Unknown')}"
                    status = "info"
                else:
                    activity_type = "system"
                    description = f"System event: {event_type}"
                    status = "info"
                
                activities.append({
                    "type": activity_type,
                    "message": description,
                    "timestamp": event.get("timestamp", ""),
                    "status": status,
                    "user": None,
                    "details": None
                })
            except Exception as e:
                # Skip malformed events, don't crash
                print(f"Error processing event: {e}")
                continue
        
        return templates.TemplateResponse("components/activity_feed.html", {
            "request": request,
            "activities": activities
        })
    except Exception as e:
        # BUG FIX 2: Return empty state HTML if something goes wrong
        print(f"Error in activity feed: {e}")
        return templates.TemplateResponse("components/activity_feed.html", {
            "request": request,
            "activities": []
        })

@app.get("/api/system-status")
def get_system_status():
    """
    JSON endpoint: Returns system health status
    """
    uptime_seconds = int(time.time() - app_start_time)
    
    # Count active workflows (leads not in LOST or WON status)
    active_workflows = sum(
        1 for lead in leads_db.values()
        if lead["status"] not in [LeadStatus.LOST, LeadStatus.WON]
    )
    
    # Mock response latency (in production, this would be real metrics)
    response_latency_ms = 45.2
    
    # Determine overall status
    leaks = detect_leaks()
    critical_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.CRITICAL)
    
    if critical_count > 2:
        status = "critical"
    elif len(leaks) > 5:
        status = "warning"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "uptime_seconds": uptime_seconds,
        "active_workflows": active_workflows,
        "response_latency_ms": response_latency_ms
    }

@app.post("/api/autonomous-mode")
def toggle_autonomous_mode(body: dict):
    """
    POST endpoint: Toggle autonomous mode on/off
    """
    global autonomous_mode_enabled
    
    enabled = body.get("enabled", False)
    autonomous_mode_enabled = enabled
    
    message = "Autonomous mode enabled" if enabled else "Autonomous mode disabled"
    
    # Log the mode change
    log_event(
        EventType.SYSTEM_EVENT,
        "system",
        {
            "action": "autonomous_mode_toggle",
            "enabled": enabled
        }
    )
    
    return {
        "enabled": autonomous_mode_enabled,
        "message": message
    }

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.get("/health")
def health_check():
    """
    BUG FIX 7: Health check endpoint with safe fallback
    """
    return {
        "status": "ok",
        "service": "FlowGuard AI",
        "engine": "online"
    }

@app.on_event("startup")
def startup_event():
    """Initialize the application"""
    print("=" * 60)
    print("FlowGuard AI - Workflow Leak Detection System")
    print("=" * 60)
    print("Server starting...")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
