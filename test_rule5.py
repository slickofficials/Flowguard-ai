import requests
import json

# Create a lead with repeated status
lead_data = {
    'name': 'Test Lead - Repeated Status',
    'message': 'Testing repeated status detection',
    'owner': 'Test Owner'
}
r = requests.post('http://localhost:8000/lead', json=lead_data)
lead = r.json()
lead_id = lead['id']
print(f'Created lead: {lead_id}')

# Add multiple workflow steps with the same status
for i in range(4):
    step_data = {
        'lead_id': lead_id,
        'step': f'Contacted attempt {i+1}',
        'status': 'contacted'
    }
    requests.post('http://localhost:8000/update-step', json=step_data)
    print(f'Added step {i+1}: Contacted attempt {i+1}')

# Check for leaks
r = requests.get('http://localhost:8000/leaks')
leaks = r.json()

# Find Rule 5 leak
rule5_leak = None
for leak in leaks['detected_leaks']:
    if leak['rule_id'] == 'RULE_005':
        rule5_leak = leak
        break

if rule5_leak:
    print('\n✓ Rule 5 (Repeated Status Detection) triggered!')
    print(json.dumps(rule5_leak, indent=2))
else:
    print('\n✗ Rule 5 not triggered')
    print(f'Total leaks: {leaks["total_leaks"]}')

# Made with Bob
