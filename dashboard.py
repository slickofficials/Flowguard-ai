from typing import List
from models import LeakDetection, RecoveryAction, LeakSeverity

# ============================================================================
# DASHBOARD HTML GENERATION
# ============================================================================

def generate_dashboard_html(
    total_leads: int,
    leaks: List[LeakDetection],
    recovery_actions: List[RecoveryAction]
) -> str:
    """
    Generate the dashboard HTML with leaks and recovery actions
    
    Args:
        total_leads: Total number of leads in the system
        leaks: List of detected leaks
        recovery_actions: List of recovery actions
        
    Returns:
        Complete HTML string for the dashboard
    """
    total_leaks = len(leaks)
    critical_count = sum(1 for leak in leaks if leak.severity == LeakSeverity.CRITICAL)
    
    # Severity color mapping
    severity_colors = {
        "critical": "#dc2626",  # red
        "high": "#ea580c",      # orange
        "medium": "#eab308",    # yellow
        "low": "#6b7280"        # gray
    }
    
    # Build leaks HTML
    leaks_html = ""
    for leak in leaks:
        color = severity_colors.get(leak.severity.value, "#6b7280")
        leaks_html += f"""
        <div style="background: white; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">{leak.lead_name}</h3>
                <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase;">{leak.severity.value}</span>
            </div>
            <p style="margin: 4px 0; color: #6b7280; font-size: 14px;"><strong>Type:</strong> {leak.type.value.replace('_', ' ').title()}</p>
            <p style="margin: 4px 0; color: #374151; font-size: 14px;">{leak.description}</p>
        </div>
        """
    
    if not leaks_html:
        leaks_html = '<p style="color: #6b7280; text-align: center; padding: 32px;">No workflow leaks detected. All systems operational! ✓</p>'
    
    # Build recovery actions HTML
    actions_html = ""
    for action in recovery_actions:
        priority_label = f"Priority {action.priority + 1}"
        priority_color = "#dc2626" if action.priority == 0 else "#ea580c" if action.priority == 1 else "#3b82f6"
        actions_html += f"""
        <div style="background: white; padding: 16px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid {priority_color};">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #111827;">{action.action_type.replace('_', ' ').title()}</h3>
                <span style="background: {priority_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">{priority_label}</span>
            </div>
            <p style="margin: 4px 0; color: #374151; font-size: 14px;">{action.description}</p>
        </div>
        """
    
    if not actions_html:
        actions_html = '<p style="color: #6b7280; text-align: center; padding: 32px;">No recovery actions needed.</p>'
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>FlowGuard AI Dashboard</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 24px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 32px;
            }}
            .header h1 {{
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .header p {{
                font-size: 18px;
                opacity: 0.9;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 16px;
                margin-bottom: 32px;
            }}
            .stat-card {{
                background: white;
                padding: 24px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .stat-card h2 {{
                font-size: 14px;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }}
            .stat-card .value {{
                font-size: 36px;
                font-weight: 700;
                color: #111827;
            }}
            .section {{
                background: rgba(255, 255, 255, 0.95);
                padding: 24px;
                border-radius: 12px;
                margin-bottom: 24px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .section h2 {{
                font-size: 24px;
                font-weight: 700;
                color: #111827;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #e5e7eb;
            }}
            .footer {{
                background: rgba(255, 255, 255, 0.95);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                color: #374151;
                font-size: 14px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .footer strong {{
                color: #111827;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>FlowGuard AI — Workflow Recovery Engine</h1>
                <p>Real-time leak detection and automated recovery</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h2>Total Leads</h2>
                    <div class="value">{total_leads}</div>
                </div>
                <div class="stat-card">
                    <h2>Total Leaks</h2>
                    <div class="value">{total_leaks}</div>
                </div>
                <div class="stat-card">
                    <h2>Critical Leaks</h2>
                    <div class="value" style="color: #dc2626;">{critical_count}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>🔴 Broken Workflows</h2>
                {leaks_html}
            </div>
            
            <div class="section">
                <h2>⚡ Recovery Actions</h2>
                {actions_html}
            </div>
            
            <div class="footer">
                <strong>Example:</strong> Client A had no owner. FlowGuard detected the leak and generated an owner assignment action.
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

# Made with Bob
