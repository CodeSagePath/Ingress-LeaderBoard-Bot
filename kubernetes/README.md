# Kubernetes Deployment Manifests

This directory contains Kubernetes manifests for deploying the Ingress Prime Leaderboard Bot in production and staging environments.

## Files Overview

- `namespace.yaml` - Namespaces for production and staging
- `configmap.yaml` - Configuration maps for both environments
- `secrets.yaml` - Secret templates (requires actual secrets)
- `deployment.yaml` - Deployment specifications for the bot
- `service.yaml` - Service definitions for exposing the bot
- `ingress.yaml` - Ingress configuration for external access
- `hpa.yaml` - Horizontal Pod Autoscaler configuration

## Deployment Instructions

### Prerequisites

1. Kubernetes cluster (v1.20+)
2. Ingress controller (nginx recommended)
3. cert-manager for SSL certificates
4. PostgreSQL database
5. Redis for caching

### 1. Prepare Secrets

Update the `secrets.yaml` file with your actual encoded secrets:

```bash
# Generate and encode secrets
echo -n "your_telegram_bot_token" | base64
echo -n "your_database_password" | base64
openssl rand -base64 32 | base64
```

### 2. Deploy to Staging

```bash
# Deploy staging environment
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

### 3. Deploy to Production

```bash
# Deploy production environment
kubectl apply -f deployment.yaml -n ingress-leaderboard
kubectl apply -f service.yaml -n ingress-leaderboard
kubectl apply -f ingress.yaml -n ingress-leaderboard
kubectl apply -f hpa.yaml -n ingress-leaderboard
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n ingress-leaderboard
kubectl get pods -n ingress-leaderboard-staging

# Check services
kubectl get services -n ingress-leaderboard

# Check ingress
kubectl get ingress -n ingress-leaderboard

# Check HPA
kubectl get hpa -n ingress-leaderboard
```

## Configuration

### Environment Variables

Key environment variables that can be configured:

- `ENVIRONMENT` - Environment name (production/staging)
- `PRODUCTION` - Production mode flag
- `DEBUG` - Debug mode flag
- `LOG_LEVEL` - Logging level
- `MONITORING_ENABLED` - Enable monitoring
- `METRICS_PORT` - Metrics port (default: 9090)
- `TELEGRAM_WEBHOOK_PORT` - Webhook port (default: 8443)

### Resource Limits

- **Production**: 256Mi/512Mi memory, 250m/500m CPU
- **Staging**: 128Mi/256Mi memory, 100m/250m CPU

### Autoscaling

- **Production**: 2-10 replicas based on CPU/memory usage
- **Staging**: Fixed 1 replica

### Health Checks

- Liveness probe: `/health` endpoint
- Readiness probe: `/health` endpoint
- Startup probe: `/health` endpoint

## Monitoring

The deployment includes:

- Prometheus metrics scraping
- Health check endpoints
- Application logs
- Resource usage monitoring

Metrics are available at:
- Production: `https://metrics.your-domain.com/metrics`
- Staging: `https://staging-metrics.your-domain.com/metrics`

## SSL/TLS

SSL certificates are automatically managed by cert-manager using Let's Encrypt:

- Production: `letsencrypt-prod` issuer
- Staging: `letsencrypt-staging` issuer

## Security

- Non-root containers (UID/GID 1000)
- Read-only root filesystem (where possible)
- Resource limits
- Network policies (recommended)
- Pod security policies (recommended)

## Backup

Database backups should be configured separately using:

- PostgreSQL native backups
- Volume snapshots
- External backup solutions

## Troubleshooting

### Common Issues

1. **Pods not starting**
   - Check secrets are properly configured
   - Verify image is available in registry
   - Check resource limits

2. **Ingress not working**
   - Verify ingress controller is running
   - Check DNS configuration
   - Validate certificate issuance

3. **Health checks failing**
   - Check application logs
   - Verify metrics port is accessible
   - Check network policies

### Useful Commands

```bash
# View logs
kubectl logs -f deployment/ingress-leaderboard-bot -n ingress-leaderboard

# Debug pod
kubectl exec -it <pod-name> -n ingress-leaderboard -- /bin/bash

# Check events
kubectl get events -n ingress-leaderboard --sort-by='.lastTimestamp'

# Port forward for testing
kubectl port-forward service/bot-service 8443:8443 -n ingress-leaderboard
```

## Updates

To update the application:

1. Build and push new Docker image
2. Update image tag in deployment.yaml
3. Apply the changes:
   ```bash
   kubectl apply -f deployment.yaml -n ingress-leaderboard
   ```

The deployment will perform a rolling update with zero downtime.