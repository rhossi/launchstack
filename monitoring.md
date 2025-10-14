```shell
# Install Prometheus + Grafana via kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install in monitoring namespace
kubectl create namespace monitoring

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80

# Login at http://localhost:3001
# Username: admin, Password: admin
```