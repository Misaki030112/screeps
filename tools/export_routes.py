"""Export remote routes from metrics/road_plan.json (written by tools/road_plan.py) to src/layouts/remote_routes.js."""
import json
d = json.load(open('metrics/road_plan.json'))
data = {'W45N8': d['r8'], 'W45N7': d['r7']}
open('src/layouts/remote_routes.js', 'w').write(
    "// Generated from metrics/road_plan.json (tools/road_plan.py). Remote haul routes, storage -> remote container.\n"
    "// Regenerate: python3 tools/export_routes.py\nmodule.exports = " + json.dumps(data, separators=(',', ':')) + ";\n")
