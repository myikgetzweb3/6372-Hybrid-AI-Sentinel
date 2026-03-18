import os, sys, json
sys.path.append(os.path.join(os.getcwd(), 'src'))
import utils
pid = utils.is_monitor_running()
status = f"🟢 ACTIVE (PID: {pid})" if pid else "🔴 INACTIVE"
print(f"Audit Status: {status}")
