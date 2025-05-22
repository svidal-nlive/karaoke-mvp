import yaml
from pathlib import Path

# Backup original
compose_path = Path('docker-compose.yml')
backup_path = compose_path.with_suffix('.yml.bak')
compose_path.replace(backup_path)

with open(backup_path, 'r') as f:
    data = yaml.safe_load(f)

# List services using local Dockerfile builds (edit as needed)
local_build_services = [
    "watcher", "metadata", "splitter", "packager", "organizer", "status-api",
    "maintenance", "maintenance-cron", "telegram_youtube_bot"
]

for svc in local_build_services:
    svc_def = data.get('services', {}).get(svc)
    if svc_def and 'build' in svc_def:
        # Set build context and dockerfile explicitly
        svc_def['build'] = {
            'context': '.',
            'dockerfile': f"{svc.replace('_', '-')}/Dockerfile" if svc not in ['maintenance', 'maintenance-cron'] else 'maintenance/Dockerfile'
        }
        # Remove shared_utils volume if present
        if 'volumes' in svc_def:
            svc_def['volumes'] = [
                v for v in svc_def['volumes']
                if not (isinstance(v, str) and ("/app/shared" in v or "./shared" in v))
            ]

with open(compose_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print(f"Updated {compose_path} (original backed up as {backup_path})")
