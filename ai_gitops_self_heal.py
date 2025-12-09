import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sklearn.ensemble import IsolationForest
import numpy as np

# CONFIG
NAMESPACE = "default"
DEPLOYMENT = "flask-app"
ARGO_APP = "flask-app"
ERROR_THRESHOLD = 30  # rule-based threshold

def run_cmd(cmd, check=True, capture_output=True, text=True):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, check=False,
                            capture_output=capture_output, text=text)
    if check and result.returncode != 0:
        print(f"Command failed (rc={result.returncode}): {result.stderr.strip()}")
        sys.exit(result.returncode)
    return result.stdout

def get_flask_logs(lines=500):
    cmd = f"kubectl logs deployment/{DEPLOYMENT} -n {NAMESPACE} --tail={lines}"
    return run_cmd(cmd)

def count_errors(logs: str) -> int:
    #return sum(1 for line in logs.splitlines() if "ERROR" in line or "Exception" in line)
    patterns = ("ERROR:", "Exception on /", "RuntimeError: AI GitOps injected failure")
    return sum(
        1
        for line in logs.splitlines()
        if any(p in line for p in patterns)
    )

def detect_anomaly(error_count: int) -> bool:
    # Very simple Isolation Forest on a tiny synthetic series
    # (in a real system you’d train on historical data)
    baseline = [0, 1, 2, 0, 1, 3, 0]  # mostly healthy baseline
    data = np.array(baseline + [error_count]).reshape(-1, 1)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(data[:-1])
    pred = model.predict(data)[-1]  # last point (current error_count)
    print(f"IsolationForest prediction for error_count={error_count}: {pred} (-1=anomaly)")
    return pred == -1

def rollback_with_argocd():
    cmd = f"argocd app rollback {ARGO_APP} 1"
    run_cmd(cmd, check=False)  # tolerate non-zero (for demo)
    print("✅ Triggered Argo CD rollback command.")

def main():
    print(f"[{datetime.utcnow().isoformat()}] Fetching Flask logs via kubectl...")
    logs = get_flask_logs(500)
    error_count = count_errors(logs)
    print(f"Current ERROR count in last 500 lines: {error_count}")

    if error_count == 0:
        print("ℹ️ No ERROR logs found, nothing to do.")
        return

    # Rule-based detection
    rule_alert = error_count >= ERROR_THRESHOLD
    print(f"Rule-based spike? {rule_alert} (threshold={ERROR_THRESHOLD})")

    # ML-based detection
    ml_alert = detect_anomaly(error_count)

    if rule_alert or ml_alert:
        print("🚨 Anomaly detected in Flask ERROR logs!")
        rollback_with_argocd()
    else:
        print("✅ No significant anomaly detected; no rollback triggered.")

if __name__ == "__main__":
    main()
