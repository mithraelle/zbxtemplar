import yaml
from zbxtemplar.executor.operations.ActionOperation import ActionOperation

with open('examples/sample_actions_decree.yml') as f:
    data = yaml.safe_load(f)

op = ActionOperation(api=None)
try:
    op.from_data(data['actions'])
    print("Parsed successfully!")
    for act in op._actions:
        print(f"Action: {act.name}")
        d = act.to_dict()
        print(f"To dict equals input? {d['name'] == act.name}")
except Exception as e:
    import traceback
    traceback.print_exc()
