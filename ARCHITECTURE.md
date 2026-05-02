# FlowGuard AI - System Architecture

## Overview

FlowGuard AI is a workflow leak detection and recovery system built with FastAPI, featuring real-time monitoring, autonomous recovery actions, and comprehensive audit trails.

## Core Architecture

### 1. Event-Driven Design
- **Event Spine**: All system actions generate events (lead creation, workflow updates, leak detection, recovery execution)
- **Event Log**: Centralized event storage in `events.py` with filtering by type and entity
- **Event Types**: `LEAD_CREATED`, `WORKFLOW_STEP_UPDATED`, `LEAK_DETECTED`, `RECOVERY_ACTION_CREATED`, `RECOVERY_ACTION_EXECUTED`, `SYSTEM_EVENT`

### 2. Leak Detection Engine
- **Rule-Based System**: 5 detection rules in `rules.py`
  - Rule 1: Missing owner detection (HIGH severity)
  - Rule 2: Missing follow-up detection (MEDIUM severity)
  - Rule 3: Client waiting detection (CRITICAL severity)
  - Rule 4: Stale lead detection (LOW severity)
  - Rule 5: High-value leak detection (severity based on status)
- **Risk Scoring**: Each leak assigned a risk score (0-100) based on severity and business impact
- **Real-time Analysis**: Continuous monitoring of all leads in the workflow

### 3. Recovery Action System
- **Autonomous Actions**: System generates recovery recommendations for each detected leak
- **Action Types**: Assign owner, schedule follow-up, urgent response, re-engage lead, escalate
- **Execution Tracking**: Actions tracked through pending → executed → failed states
- **Audit Trail**: Complete explainability for all recovery actions

### 4. Data Storage
- **In-Memory Storage**: Fast access using Python dictionaries
  - `leads_db`: Lead data storage
  - `workflow_steps_db`: Workflow history per lead
  - `recovery_actions_db`: Recovery action tracking
  - `events_log`: System event log
  - `audit_log`: Audit trail entries
- **Modular Design**: All storage functions in `store.py` for easy migration to persistent storage

### 5. API Layer
- **RESTful Endpoints**: FastAPI-based API with automatic OpenAPI documentation
- **HTMX Integration**: Real-time dashboard updates without full page reloads
- **JSON Responses**: Structured data for programmatic access

### 6. Dashboard UI
- **Real-time Metrics**: Event spine records, active workflow leaks, executed recovery actions, system health
- **Live Updates**: HTMX polling for automatic data refresh (5-15 second intervals)
- **Component-Based**: Modular HTML components for metrics, incidents, task queue, activity feed
- **Responsive Design**: TailwindCSS-based styling with glassmorphism effects

## Module Breakdown

### Core Modules
- **main.py**: FastAPI application, API endpoints, HTMX handlers
- **models.py**: Pydantic models for data validation and serialization
- **store.py**: In-memory data storage and access functions
- **rules.py**: Leak detection rules and risk scoring logic
- **recovery.py**: Recovery action generation and recommendations
- **events.py**: Event logging and retrieval system
- **audit.py**: Audit trail for explainability and compliance
- **impact.py**: Business impact analysis and reporting
- **dashboard.py**: Dashboard HTML generation (legacy, now using templates)

### Template System
- **templates/base.html**: Base layout with navigation and styling
- **templates/dashboard.html**: Main dashboard page structure
- **templates/components/**: Reusable HTMX components
  - `metrics.html`: Key performance indicators
  - `incidents.html`: Active workflow leaks display
  - `task_queue.html`: Recovery actions queue
  - `activity_feed.html`: Real-time event stream

### Static Assets
- **static/css/styles.css**: Custom styles and animations
- **static/js/app.js**: Client-side JavaScript for interactivity

## Data Flow

1. **Lead Creation** → Event logged → Stored in leads_db → Workflow step added
2. **Leak Detection** → Rules analyze leads → Leaks identified → Events logged → Audit trail created
3. **Recovery Generation** → Actions created for leaks → Stored in recovery_actions_db → Events logged
4. **Action Execution** → Status updated → Timestamp recorded → Event logged → Audit trail updated
5. **Dashboard Display** → HTMX polls APIs → Components updated → Real-time visualization

## Key Design Decisions

### Why Event-Driven?
- **Auditability**: Complete history of all system actions
- **Debugging**: Easy to trace issues through event log
- **Analytics**: Rich data for business intelligence
- **Extensibility**: Easy to add new event consumers

### Why In-Memory Storage?
- **Speed**: Instant access for real-time monitoring
- **Simplicity**: No database setup required for demo
- **Portability**: Easy to run anywhere Python is available
- **Migration Path**: Clear separation allows easy database integration

### Why HTMX?
- **Simplicity**: No complex JavaScript framework needed
- **Performance**: Minimal client-side processing
- **Progressive Enhancement**: Works without JavaScript
- **Real-time Updates**: Automatic polling for live data

## Scalability Considerations

### Current Limitations
- In-memory storage (data lost on restart)
- Single-process architecture
- No authentication/authorization
- Limited to single-server deployment

### Production Enhancements
1. **Database Integration**: PostgreSQL for persistent storage
2. **Caching Layer**: Redis for high-frequency data
3. **Message Queue**: RabbitMQ/Kafka for event processing
4. **Load Balancing**: Multiple API servers behind load balancer
5. **Authentication**: OAuth2/JWT for secure access
6. **Monitoring**: Prometheus/Grafana for observability
7. **Logging**: Structured logging with ELK stack

## Security Features

- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: Graceful degradation on failures
- **Audit Trail**: Complete record of all actions
- **Explainability**: Clear reasoning for all decisions

## Testing Strategy

- **Unit Tests**: Individual rule testing (e.g., `test_rule5.py`)
- **Integration Tests**: End-to-end workflow testing
- **Demo Data**: `/seed-demo` endpoint for consistent testing
- **Manual Testing**: Interactive dashboard for visual verification

## Future Enhancements

1. **Machine Learning**: Predictive leak detection
2. **Workflow Automation**: Automatic action execution
3. **Multi-tenant Support**: Isolated data per organization
4. **Advanced Analytics**: Trend analysis and forecasting
5. **Integration APIs**: Connect to CRM systems
6. **Mobile App**: Native mobile dashboard
7. **Notification System**: Email/SMS alerts for critical leaks

## Performance Metrics

- **API Response Time**: < 50ms for most endpoints
- **Dashboard Refresh**: 5-15 second intervals
- **Leak Detection**: Real-time analysis on data changes
- **Event Processing**: Asynchronous, non-blocking

## Deployment

### Requirements
- Python 3.8+
- FastAPI
- Uvicorn
- Jinja2
- Pydantic

### Running Locally
```bash
cd flowguard-ai
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Access Points
- Dashboard: http://localhost:8000/dashboard
- API Docs: http://localhost:8000/docs
- Seed Demo: http://localhost:8000/seed-demo

---

**Built with FastAPI, HTMX, and TailwindCSS**