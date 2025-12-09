# python-kube-demo

```markdown
# AI GitOps Self-Healing Demo (Flask + Argo CD)

This project is a small SRE / Platform Engineering lab that shows how GitOps and basic ML can automatically roll back a bad Kubernetes deployment.

## Architecture

- Flask web app running on Kubernetes (`flask-app` Deployment, `flask-service` Service).
- Logs read directly via `kubectl logs deployment/flask-app`.
- `ai_gitops_self_heal.py`:
  - Counts ERROR lines and runs an Isolation Forest model on recent logs.
  - On anomaly, calls `argocd app rollback flask-app 1`.
- Argo CD Application `flask-app`:
  - Syncs manifests from this repo.
  - Shows app health and rollback history.

## How to Run the Demo

1. **Prerequisites**

   - Minikube or Kubernetes cluster.
   - Argo CD installed and configured.
   - `kubectl`, `argocd`, and `python3` with `requirements.txt` installed.

2. **Deploy the app via Argo CD**

   - Add this repo as an Argo CD Application pointing to the `.` path.
   - Sync the app:
     ```
     argocd app sync flask-app
     ```

3. **Trigger a bad version**

   - Build and push a bad image tag (with a failing `app.py` that logs errors).
   - Point the Deployment at that tag:
     ```
     kubectl set image deployment/flask-app \
       flask-app=docker.io/<your-user>/flask-app:bad \
       -n default
     ```

4. **Generate traffic and confirm errors**

   ```
   for i in {1..50}; do
     curl -s http://flask-app.default.svc.cluster.local/ || true
     sleep 0.05
   done

   kubectl logs deployment/flask-app -n default --tail=80
   ```

5. **Run self-healing**

   ```
   python3 ai_gitops_self_heal.py
   ```

   Expected:
   - Non-zero ERROR count.
   - Anomaly detected (rule + Isolation Forest).
   - `argocd app rollback flask-app 1` executed.

6. **Verify rollback**

   ```
   argocd app get flask-app | grep -E 'Sync Status|Health Status|Revision|Name:'
   kubectl logs deployment/flask-app -n default --tail=40
   ```

   You should see a healthy app with no injected errors.

## Files

- `app.py` – Flask app.
- `app-deployment.yaml` – Kubernetes Deployment.
- `flask-service.yaml` – Service exposing the app.
- `ai_gitops_self_heal.py` – Log anomaly detection + Argo CD rollback.
- `requirements.txt` – Python dependencies.
```
