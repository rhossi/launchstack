# Step by step process to install Prometheus and Graphana and expose it via Load Balancer Service

## Create a namespace 

```
kubectl create ns monitoring
```

## Install Prometheus within the namespace and set the password
```
helm install prometheus prometheus-community/prometheus\\n  --namespace monitoring \\n  --set grafana.adminPassword=admin
```

## Add grafana helm repo and update helm
```
helm repo add grafana https://grafana.github.io/helm-charts \nhelm repo update
```

## Install Grafana within the namespace and set the password
```
helm install grafana grafana/grafana \\n  --namespace monitoring \\n  --set grafana.adminPassword=admin
```

## Expose both Prometheus and Grafana with a Load Balancer to be able access from the internet
```
kubectl expose service grafana --type=LoadBalancer --target-port=3000 --name=grafana-ext -n monitoring
kubectl expose service prometheus-server --type=LoadBalancer --target-port=9090 --name=prometheus-server-ext -n monitoring
```

## Optional- only for your reference

## If you would like to check the admin password
```
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

## Steps to uninstall
```
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring
helm repo remove prometheus-community
```

_Created by Saipriya Thirvakadu - October 14, 2025_

_Reference: https://medium.com/@gayatripawar401/deploy-prometheus-and-grafana-on-kubernetes-using-helm-5aa9d4fbae66_


