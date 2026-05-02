# FlowGuard AI 🛡️

**FlowGuard AI** is an intelligent workflow leak detection system that monitors business processes in real-time and automatically identifies potential bottlenecks, delays, and process failures. Built with Python and FastAPI, it helps teams prevent revenue loss by catching workflow issues before they become critical problems.

## 🚀 Features

FlowGuard AI detects four critical types of workflow leaks:

1. **Missing Owner Detection** - Identifies leads without assigned owners and triggers automatic assignment alerts
2. **Missing Follow-up Detection** - Catches leads with no activity for 24+ hours and suggests immediate follow-up actions
3. **Client Waiting Detection** - Flags leads in "waiting" status as critical priority to prevent client churn
4. **Stale Lead Detection** - Identifies leads that remain in "new" status for 72+ hours and recommends reactivation

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## 🔧 Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd flowguard-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   This will install:
   - `fastapi` - Modern web framework for building APIs
   - `uvicorn[standard]` - ASGI server for running the application
   - `pydantic` - Data validation using Python type annotations

## ▶️ Running the Application

Start the FlowGuard AI server using uvicorn:

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

**Access the interactive API documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📡 API Endpoints

### 1. Root Endpoint
**GET /** - Get API information and available endpoints

**Response:**
```json
{
  "service": "FlowGuard AI",
  "version": "1.0.0",
  "description": "Workflow Leak Detection System",
  "endpoints": {
    "POST /lead": "Create a new lead",
    "POST /update-step": "Update workflow step for a lead",
    "GET /status": "Get current workflow state for all leads",
    "GET /leaks": "Get detected leaks with recovery actions"
  }
}
```

### 2. Create Lead
**POST /lead** - Create a new lead in the system

**Request Body:**
```json
{
  "name": "John Doe",
  "message": "Interested in enterprise plan",
  "owner": "Sarah Johnson"
}
```

**Response:**
```json
{
  "id": "a1b2c3d4",
  "name": "John Doe",
  "message": "Interested in enterprise plan",
  "owner": "Sarah Johnson",
  "status": "new",
  "created_at": "2026-05-02T07:30:00.000Z",
  "last_updated": "2026-05-02T07:30:00.000Z",
  "workflow_steps": ["Lead created"]
}
```

### 3. Update Workflow Step
**POST /update-step** - Add a workflow step to a lead

**Request Body:**
```json
{
  "lead_id": "a1b2c3d4",
  "step": "Initial contact made via email",
  "status": "contacted"
}
```

**Response:**
```json
{
  "success": true,
  "lead_id": "a1b2c3d4",
  "step_added": "Initial contact made via email",
  "new_status": "contacted",
  "timestamp": "2026-05-02T08:15:00.000Z"
}
```

### 4. Get Workflow Status
**GET /status** - Get current state of all leads

**Response:**
```json
{
  "total_leads": 3,
  "workflow_state": [
    {
      "id": "a1b2c3d4",
      "name": "John Doe",
      "message": "Interested in enterprise plan",
      "owner": "Sarah Johnson",
      "status": "contacted",
      "created_at": "2026-05-02T07:30:00.000Z",
      "last_updated": "2026-05-02T08:15:00.000Z",
      "workflow_steps": [
        "Lead created",
        "Initial contact made via email"
      ]
    }
  ],
  "summary": {
    "new": 1,
    "contacted": 1,
    "waiting": 1
  }
}
```

### 5. Get Detected Leaks
**GET /leaks** - Analyze workflow and detect leaks with recovery actions

**Response:**
```json
{
  "total_leaks": 2,
  "detected_leaks": [
    {
      "leak_id": "x7y8z9w0",
      "type": "client_waiting",
      "lead_id": "b2c3d4e5",
      "lead_name": "Jane Smith",
      "severity": "critical",
      "description": "Lead 'Jane Smith' is in WAITING status - client may be blocked",
      "detected_at": "2026-05-02T09:00:00.000Z"
    },
    {
      "leak_id": "p1q2r3s4",
      "type": "missing_followup",
      "lead_id": "c3d4e5f6",
      "lead_name": "Bob Wilson",
      "severity": "high",
      "description": "Lead 'Bob Wilson' has no follow-up action for 36 hours",
      "detected_at": "2026-05-02T09:00:00.000Z"
    }
  ],
  "recovery_actions": [
    {
      "action_id": "m5n6o7p8",
      "leak_id": "x7y8z9w0",
      "action_type": "urgent_response",
      "description": "URGENT: Contact lead 'Jane Smith' immediately to unblock",
      "priority": 0
    },
    {
      "action_id": "q9r0s1t2",
      "leak_id": "p1q2r3s4",
      "action_type": "schedule_followup",
      "description": "Schedule immediate follow-up call/email for lead 'Bob Wilson'",
      "priority": 1
    }
  ]
}
```

## 🔍 Detection Rules

FlowGuard AI uses intelligent rules to detect workflow leaks:

### 1. Missing Owner Detection
- **Trigger:** Lead created without an assigned owner
- **Severity:** Medium
- **Action:** Auto-assigns "Auto-assigned Agent" and flags for manual assignment
- **Recovery:** Manually assign a qualified owner to the lead

### 2. Missing Follow-up Detection
- **Trigger:** No workflow activity for 24+ hours on active leads
- **Severity:** High
- **Action:** Flags lead for immediate follow-up
- **Recovery:** Schedule urgent call or email to re-engage the lead

### 3. Client Waiting Detection
- **Trigger:** Lead status is "waiting"
- **Severity:** Critical
- **Action:** Highest priority alert - client may be blocked
- **Recovery:** Immediate contact required to unblock and move forward

### 4. Stale Lead Detection
- **Trigger:** Lead remains in "new" status for 72+ hours
- **Severity:** High
- **Action:** Flags lead as stale and at risk of being lost
- **Recovery:** Review lead, attempt reactivation, or mark as closed-lost

## 💡 Example Usage

### Create a lead without owner (triggers leak detection):
```bash
curl -X POST "http://localhost:8000/lead" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Cooper",
    "message": "Need pricing for 100 users"
  }'
```

### Create a lead with owner:
```bash
curl -X POST "http://localhost:8000/lead" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Martin",
    "message": "Interested in demo",
    "owner": "Mike Sales"
  }'
```

### Update workflow step:
```bash
curl -X POST "http://localhost:8000/update-step" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "a1b2c3d4",
    "step": "Demo scheduled for tomorrow",
    "status": "qualified"
  }'
```

### Check for leaks:
```bash
curl -X GET "http://localhost:8000/leaks"
```

### View all leads status:
```bash
curl -X GET "http://localhost:8000/status"
```

## 📁 Project Structure

```
flowguard-ai/
├── main.py              # Main application with FastAPI endpoints and leak detection logic
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🎯 Lead Status Flow

Leads progress through the following statuses:

1. **new** - Lead just created
2. **contacted** - Initial contact made
3. **qualified** - Lead meets qualification criteria
4. **waiting** - Waiting for client response or action
5. **negotiating** - In active negotiation
6. **closed_won** - Successfully closed
7. **closed_lost** - Lost opportunity

## 🛠️ Technology Stack

- **FastAPI** - High-performance Python web framework
- **Pydantic** - Data validation and settings management
- **Uvicorn** - Lightning-fast ASGI server
- **Python 3.7+** - Modern Python with type hints

## 📝 Notes

- All data is stored in-memory (resets on server restart)
- Timestamps are in ISO 8601 UTC format
- Lead IDs are auto-generated 8-character UUIDs
- Recovery actions are sorted by priority (0 = highest)

## 🚦 Getting Started Demo

1. Start the server: `uvicorn main:app --reload`
2. Open the interactive docs: `http://localhost:8000/docs`
3. Create a few leads (some with owners, some without)
4. Update workflow steps for some leads
5. Check `/leaks` endpoint to see detected issues
6. View `/status` to see complete workflow state

---

**Made with Bob** 🤖