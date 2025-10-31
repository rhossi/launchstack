# Prometheus + Grafana Monitoring Stack

Complete Kubernetes cluster monitoring with Prometheus and Grafana using the kube-prometheus-stack Helm chart.

> **📖 [Back to Launchstack Overview](../README.md)** | This is Step 2 of the [Launchstack](https://github.com/yourusername/launchstack) deployment sequence.

---

## QUICKSTART

Everything you need to get monitoring running in your cluster.

### Prerequisites

Before installing, ensure you have:

- A running Kubernetes cluster
- `kubectl` configured to access your cluster
- `helm` CLI installed (v3.x or later)
- Sufficient cluster resources (recommended: at least 4GB RAM, 2 CPUs available)

### Installation Steps

#### Step 1: Add Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

#### Step 2: Create Monitoring Namespace

```bash
kubectl create namespace monitoring
```

#### Step 3: Install kube-prometheus-stack

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword=admin
```

> **Note**: Change `admin` to a strong password for production.

#### Step 4: Verify Installation

Check that all pods are running:

```bash
kubectl get pods -n monitoring
```

You should see pods for:

- prometheus-operator
- prometheus-server
- grafana
- node-exporter
- kube-state-metrics

### Accessing Grafana

#### Local Access

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80
```

Open **<http://localhost:3001>** in your browser.

#### Login Credentials

- **Username**: `admin`
- **Password**: `admin` (or the password you set during installation)

### What's Included

The installation deploys:

- **Prometheus Operator**: Manages Prometheus and Alertmanager instances
- **Prometheus**: Time-series database for metrics
- **Grafana**: Visualization and dashboarding platform
- **Node Exporter**: Hardware and OS metrics
- **Kube State Metrics**: Kubernetes cluster state metrics
- **Pre-configured Dashboards**: Ready-to-use Grafana dashboards

### Explore Dashboards

Grafana includes pre-configured dashboards:

1. Navigate to **Dashboards** → **Browse**
2. Check out dashboards like:
   - Kubernetes / Compute Resources / Cluster
   - Kubernetes / Compute Resources / Namespace (Pods)
   - Node Exporter / Nodes

---

## CUSTOMIZATION

Optional configurations for production, scaling, and advanced use cases.

### Table of Contents

- [Configuration Options](#configuration-options)
- [Common Customizations](#common-customizations)
- [Production Setup](#production-setup)
- [Accessing Prometheus](#accessing-prometheus)
- [Custom Dashboards](#custom-dashboards)
- [Alerting](#alerting)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Resources](#resources)

---

### Configuration Options

#### Viewing All Available Options

To see all configuration options:

```bash
helm show values prometheus-community/kube-prometheus-stack > custom-values.yaml
```

#### Applying Configuration Changes

After modifying `custom-values.yaml`:

```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values custom-values.yaml
```

---

### Common Customizations

#### 1. Enable Persistence for Prometheus

```yaml
prometheus:
  prometheusSpec:
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: fast-ssd
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
```

#### 2. Enable Persistence for Grafana

```yaml
grafana:
  persistence:
    enabled: true
    storageClassName: fast-ssd
    accessModes:
      - ReadWriteOnce
    size: 10Gi
```

#### 3. Adjust Resource Limits

```yaml
prometheus:
  prometheusSpec:
    resources:
      requests:
        memory: 2Gi
        cpu: 1000m
      limits:
        memory: 4Gi
        cpu: 2000m

grafana:
  resources:
    requests:
      memory: 256Mi
      cpu: 250m
    limits:
      memory: 512Mi
      cpu: 500m
```

#### 4. Configure Ingress for Grafana

```yaml
grafana:
  ingress:
    enabled: true
    ingressClassName: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - grafana.yourdomain.com
    tls:
      - secretName: grafana-tls
        hosts:
          - grafana.yourdomain.com
```

#### 5. Configure Ingress for Prometheus

```yaml
prometheus:
  ingress:
    enabled: true
    ingressClassName: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - prometheus.yourdomain.com
    tls:
      - secretName: prometheus-tls
        hosts:
          - prometheus.yourdomain.com
```

#### 6. Adjust Metrics Retention

```yaml
prometheus:
  prometheusSpec:
    retention: 30d  # Keep metrics for 30 days
    retentionSize: "45GB"  # Limit storage usage
```

#### 7. Configure Alertmanager

```yaml
alertmanager:
  config:
    global:
      resolve_timeout: 5m
    route:
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'default'
    receivers:
      - name: 'default'
        email_configs:
          - to: 'alerts@yourdomain.com'
            from: 'prometheus@yourdomain.com'
            smarthost: 'smtp.yourdomain.com:587'
            auth_username: 'prometheus@yourdomain.com'
            auth_password: 'your-password'
```

#### 8. Enable Additional Scrape Configs

```yaml
prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
      - job_name: 'custom-app'
        static_configs:
          - targets: ['app.namespace.svc.cluster.local:8080']
```

---

### Production Setup

#### Complete Production Example

```yaml
# custom-values.yaml
grafana:
  adminPassword: "strong-password-here"
  
  persistence:
    enabled: true
    storageClassName: fast-ssd
    size: 10Gi
  
  ingress:
    enabled: true
    ingressClassName: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
      nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    hosts:
      - grafana.yourdomain.com
    tls:
      - secretName: grafana-tls
        hosts:
          - grafana.yourdomain.com
  
  resources:
    requests:
      memory: 512Mi
      cpu: 500m
    limits:
      memory: 1Gi
      cpu: 1000m

prometheus:
  prometheusSpec:
    replicas: 2  # High availability
    
    retention: 30d
    retentionSize: "45GB"
    
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: fast-ssd
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    
    resources:
      requests:
        memory: 4Gi
        cpu: 2000m
      limits:
        memory: 8Gi
        cpu: 4000m
    
    podAntiAffinity: soft
    
  ingress:
    enabled: true
    ingressClassName: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
      nginx.ingress.kubernetes.io/auth-type: basic
      nginx.ingress.kubernetes.io/auth-secret: prometheus-basic-auth
    hosts:
      - prometheus.yourdomain.com
    tls:
      - secretName: prometheus-tls
        hosts:
          - prometheus.yourdomain.com

alertmanager:
  alertmanagerSpec:
    replicas: 2
    
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: fast-ssd
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi

nodeExporter:
  enabled: true

kubeStateMetrics:
  enabled: true
```

#### Production Considerations

**Security:**

- Use strong passwords for Grafana admin
- Enable authentication for Prometheus and Alertmanager
- Configure RBAC properly
- Use network policies to restrict access
- Enable TLS/HTTPS for all endpoints

**High Availability:**

- Deploy multiple Prometheus replicas
- Use pod anti-affinity to spread replicas
- Configure Alertmanager in HA mode
- Use external storage for Grafana dashboards

**Performance:**

- Allocate sufficient resources based on cluster size
- Monitor Prometheus performance metrics
- Adjust retention period based on storage capacity
- Use remote write for long-term storage

**Data Management:**

- Enable persistent volumes for data retention
- Set appropriate retention periods
- Monitor storage usage
- Implement backup strategy for Grafana dashboards

**Networking:**

- Use ingress with TLS for external access
- Configure rate limiting
- Use OCI WAF for additional protection
- Set up DNS properly

---

### Accessing Prometheus

Access Prometheus UI:

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Navigate to **<http://localhost:9090>**

---

### Custom Dashboards

#### Import from Grafana Library

1. In Grafana, go to **Dashboards** → **Import**
2. Enter a dashboard ID or upload JSON file
3. Select Prometheus data source

Popular dashboard IDs:

- **1860**: Node Exporter Full
- **315**: Kubernetes Cluster Monitoring
- **12740**: Kubernetes Monitoring

#### Create Custom Dashboards

1. In Grafana, click **+** → **Dashboard**
2. Add panels with Prometheus queries
3. Save dashboard

Example PromQL queries:

```promql
# CPU usage by pod
sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)

# Memory usage by namespace
sum(container_memory_working_set_bytes) by (namespace)

# Pod restart count
kube_pod_container_status_restarts_total
```

---

### Alerting

#### View Pre-configured Alerts

Access Prometheus alerts:

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Navigate to **<http://localhost:9090/alerts>**

#### Configure Alert Notifications

Configure Alertmanager receivers in `custom-values.yaml`:

**Email Notifications:**

```yaml
alertmanager:
  config:
    receivers:
      - name: 'email'
        email_configs:
          - to: 'team@yourdomain.com'
            from: 'alertmanager@yourdomain.com'
            smarthost: 'smtp.gmail.com:587'
            auth_username: 'alertmanager@yourdomain.com'
            auth_password: 'app-password'
```

**Slack Notifications:**

```yaml
alertmanager:
  config:
    receivers:
      - name: 'slack'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
            channel: '#alerts'
            title: 'Alert: {{ .GroupLabels.alertname }}'
```

**OCI Notifications:**

```yaml
alertmanager:
  config:
    receivers:
      - name: 'oci-notifications'
        webhook_configs:
          - url: 'https://cell-1.notification.us-ashburn-1.oci.oraclecloud.com/...'
```

#### Create Custom Alerts

Add custom PrometheusRule:

```yaml
additionalPrometheusRulesMap:
  custom-alerts:
    groups:
      - name: custom
        rules:
          - alert: HighPodMemory
            expr: container_memory_usage_bytes > 1e9
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "High memory usage in pod {{ $labels.pod }}"
```

---

### Troubleshooting

#### Pods Not Starting

Check pod status:

```bash
kubectl get pods -n monitoring
kubectl describe pod -n monitoring <pod-name>
kubectl logs -n monitoring <pod-name>
```

Common issues:

- **Insufficient resources**: Check cluster has enough CPU/memory
- **Storage issues**: Verify storage class is available
- **Image pull errors**: Check network connectivity

#### Can't Access Grafana

Verify service is running:

```bash
kubectl get svc -n monitoring prometheus-grafana
```

Check port-forward:

```bash
# Ensure no firewall blocking localhost:3001
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80
```

#### Missing Metrics

Ensure ServiceMonitors are configured:

```bash
kubectl get servicemonitors -n monitoring
```

Check Prometheus targets:

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Navigate to http://localhost:9090/targets
```

#### High Memory Usage

Adjust Prometheus retention:

```yaml
prometheus:
  prometheusSpec:
    retention: 15d  # Reduce retention period
    retentionSize: "30GB"  # Set size limit
```

---

### Maintenance

#### Updating the Stack

```bash
# Update Helm repository
helm repo update

# Check available versions
helm search repo prometheus-community/kube-prometheus-stack --versions

# Upgrade to latest
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values custom-values.yaml

# Or upgrade to specific version
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values custom-values.yaml \
  --version 55.0.0
```

#### Backup Grafana Dashboards

```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3001:80

# Use Grafana API to backup dashboards
curl -u admin:password http://localhost:3001/api/search > dashboards-list.json
```

Or use Grafana UI: Settings → Export Dashboard

#### Backup Prometheus Data

For production, consider:

- Enabling persistent volumes
- Using Prometheus remote write to external storage
- Taking volume snapshots
- Using OCI Object Storage for backups

#### Uninstalling

```bash
# Uninstall Helm release
helm uninstall prometheus --namespace monitoring

# Delete namespace (removes all resources)
kubectl delete namespace monitoring
```

> **Warning**: This permanently deletes all metrics data and dashboards. Backup first!

---

### Resources

#### Official Documentation

- [kube-prometheus-stack Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)

#### Useful Links

- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)
- [Alerting Rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)

#### Community

- [Prometheus Community](https://prometheus.io/community/)
- [Grafana Community](https://community.grafana.com/)

---

Happy Monitoring! 📊
