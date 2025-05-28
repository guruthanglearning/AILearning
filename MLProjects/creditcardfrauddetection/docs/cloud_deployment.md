# Cloud Deployment Guide

This guide provides instructions for deploying the Credit Card Fraud Detection system to various cloud environments.

## AWS Deployment

### ECS Deployment (Recommended)

1. **Build and Push Docker Image to ECR**

```bash
# Create an ECR repository
aws ecr create-repository --repository-name fraud-detection-api

# Get authentication token and authenticate Docker
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com

# Build and tag the image
docker build -t fraud-detection-api .
docker tag fraud-detection-api:latest YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/fraud-detection-api:latest

# Push the image
docker push YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/fraud-detection-api:latest
```

2. **Create ECS Task Definition**

```json
{
  "family": "fraud-detection-api",
  "networkMode": "awsvpc",
  "executionRoleArn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/fraud-detection-api-role",
  "containerDefinitions": [
    {
      "name": "fraud-detection-api",
      "image": "YOUR-ACCOUNT-ID.dkr.ecr.us-east-1.amazonaws.com/fraud-detection-api:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "APP_ENV",
          "value": "production"
        },
        {
          "name": "DEBUG",
          "value": "False"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:ssm:us-east-1:YOUR-ACCOUNT-ID:parameter/fraud-detection/OPENAI_API_KEY"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:ssm:us-east-1:YOUR-ACCOUNT-ID:parameter/fraud-detection/SECRET_KEY"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fraud-detection-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      },
      "cpu": 1024,
      "memory": 2048
    }
  ],
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048"
}
```

3. **Create an ECS Service**

```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name fraud-detection-api \
  --task-definition fraud-detection-api:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:YOUR-ACCOUNT-ID:targetgroup/fraud-detection-api/abcdef1234567890,containerName=fraud-detection-api,containerPort=8000"
```

4. **Set Up Auto Scaling**

```bash
# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/your-cluster/fraud-detection-api \
  --policy-name cpu-tracking-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }'
```

### AWS Lambda Deployment (for lower volumes)

If your transaction volume is lower, you can deploy the fraud screening as a Lambda function:

1. **Create Lambda Layer with Dependencies**

```bash
# Create a directory for the layer
mkdir -p lambda-layer/python

# Install dependencies to the layer directory
pip install -r requirements.txt -t lambda-layer/python

# Create the layer zip
cd lambda-layer
zip -r ../fraud-detection-layer.zip .
cd ..
```

2. **Create Lambda Function Code**

Create a `lambda_function.py` file with your function code:

```python
import json
from app.api.models import Transaction, FraudDetectionResponse
from app.services.fraud_detection_service import FraudDetectionService

# Initialize service
fraud_service = FraudDetectionService()

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Create transaction object
        transaction = Transaction(**body)
        
        # Process transaction
        response = fraud_service.detect_fraud(transaction)
        
        # Return response
        return {
            'statusCode': 200,
            'body': json.dumps(response.dict())
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

3. **Deploy the Function**

```bash
# Create a deployment package
zip -r function.zip lambda_function.py app/

# Create the Lambda layer
aws lambda publish-layer-version \
  --layer-name fraud-detection-layer \
  --zip-file fileb://fraud-detection-layer.zip \
  --compatible-runtimes python3.9

# Create the Lambda function
aws lambda create-function \
  --function-name fraud-detection \
  --runtime python3.9 \
  --handler lambda_function.lambda_handler \
  --role arn:aws:iam::YOUR-ACCOUNT-ID:role/fraud-detection-lambda-role \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 1024 \
  --layers arn:aws:lambda:us-east-1:YOUR-ACCOUNT-ID:layer:fraud-detection-layer:1 \
  --environment "Variables={APP_ENV=production,DEBUG=False,OPENAI_API_KEY=your-key,SECRET_KEY=your-secret-key}"
```

## Google Cloud Deployment

### Google Kubernetes Engine (GKE)

1. **Build and Push the Docker Image**

```bash
# Tag the image for GCR
docker build -t gcr.io/YOUR-PROJECT-ID/fraud-detection-api:latest .

# Push to GCR
docker push gcr.io/YOUR-PROJECT-ID/fraud-detection-api:latest
```

2. **Create Kubernetes Deployment Files**

Create a file named `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fraud-detection-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fraud-detection-api
  template:
    metadata:
      labels:
        app: fraud-detection-api
    spec:
      containers:
      - name: fraud-detection-api
        image: gcr.io/YOUR-PROJECT-ID/fraud-detection-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "production"
        - name: DEBUG
          value: "False"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: fraud-detection-secrets
              key: openai-api-key
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: fraud-detection-secrets
              key: secret-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 15
---
apiVersion: v1
kind: Service
metadata:
  name: fraud-detection-api
spec:
  selector:
    app: fraud-detection-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

3. **Create Kubernetes Secrets**

```bash
kubectl create secret generic fraud-detection-secrets \
  --from-literal=openai-api-key=YOUR-OPENAI-API-KEY \
  --from-literal=secret-key=YOUR-SECRET-KEY
```

4. **Deploy to GKE**

```bash
kubectl apply -f k8s-deployment.yaml
```

5. **Set Up Horizontal Pod Autoscaling**

```bash
kubectl autoscale deployment fraud-detection-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

## Azure Deployment

### Azure Container Apps

1. **Create an Azure Container Registry and Push Image**

```bash
# Create resource group if needed
az group create --name fraud-detection-rg --location eastus

# Create container registry
az acr create --resource-group fraud-detection-rg --name frauddetectionregistry --sku Basic

# Log in to registry
az acr login --name frauddetectionregistry

# Tag image for ACR
docker tag fraud-detection-api frauddetectionregistry.azurecr.io/fraud-detection-api:latest

# Push to ACR
docker push frauddetectionregistry.azurecr.io/fraud-detection-api:latest
```

2. **Create a Container App**

```bash
# Create Container Apps environment
az containerapp env create \
  --name fraud-detection-env \
  --resource-group fraud-detection-rg \
  --location eastus

# Create the Container App
az containerapp create \
  --name fraud-detection-api \
  --resource-group fraud-detection-rg \
  --environment fraud-detection-env \
  --image frauddetectionregistry.azurecr.io/fraud-detection-api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 2 \
  --max-replicas 10 \
  --secrets "openai-api-key=YOUR-OPENAI-API-KEY" "secret-key=YOUR-SECRET-KEY" \
  --env-vars "APP_ENV=production" "DEBUG=False" "OPENAI_API_KEY=secretref:openai-api-key" "SECRET_KEY=secretref:secret-key" \
  --cpu 1.0 \
  --memory 2.0Gi \
  --registry-server frauddetectionregistry.azurecr.io
```

## Security Best Practices

When deploying to any cloud environment, follow these security best practices:

1. **API Authentication**: Ensure your API key authentication is properly configured
2. **Network Security**: 
   - Use private subnets where possible
   - Implement IP filtering/allowlisting for your API
   - Use HTTPS for all communications
3. **Secret Management**:
   - Never hard-code secrets in your code or Docker images
   - Use cloud-native secret management services (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)
4. **Monitoring and Logging**:
   - Enable detailed logging
   - Set up alerts for suspicious activities
   - Monitor API usage for rate limiting
5. **Compliance**:
   - Ensure your deployment meets financial services compliance requirements
   - Implement proper data retention policies

## Cost Optimization

To optimize costs while maintaining performance:

1. Use auto-scaling to handle variable loads
2. Consider serverless options for lower-volume implementations
3. Optimize your model inference to reduce OpenAI API costs
4. Use tiered detection to minimize LLM usage for clear-cut cases
5. Implement proper caching to reduce redundant processing
