# User Guide: NanoGPT Complete ML Platform 🚀

Welcome to the comprehensive user guide for the NanoGPT Complete ML Platform! This guide will walk you through every aspect of using the platform, from initial setup to advanced analysis.

## 📖 Table of Contents

1. [Getting Started](#-getting-started)
2. [Platform Overview](#-platform-overview)
3. [NanoGPT Dashboard](#-nanogpt-dashboard)
4. [TorchSharp Inspector](#-torchsharp-inspector)
5. [API Usage](#-api-usage)
6. [Monitoring & Analytics](#-monitoring--analytics)
7. [Troubleshooting](#-troubleshooting)
8. [Advanced Usage](#-advanced-usage)
9. [Best Practices](#-best-practices)

---

## 🚀 Getting Started

### Prerequisites Check
Before you begin, ensure you have:
- ✅ Windows 10/11 or Linux/macOS
- ✅ .NET 10.0 SDK installed
- ✅ Docker and Docker Compose
- ✅ At least 8GB RAM (16GB recommended)
- ✅ 5GB free disk space

### Quick Setup (5 minutes)

1. **Navigate to Project Directory**
   ```powershell
   cd "D:\Study\AILearning\MLProjects\AIModels\Learning\MLModelTraining_NanoGPT"
   ```

2. **One-Command Deployment**
   ```powershell
   # Windows
   .\deploy.ps1
   
   # Linux/macOS
   ./deploy.sh
   ```

3. **Verify Installation**
   - Wait for "🎉 Deployment completed successfully!" message
   - Check all services are running: `docker-compose ps`

4. **Access the Platform**
   - Dashboard: http://localhost:5169
   - TorchSharp Inspector: http://localhost:8082
   - API Documentation: http://localhost:8080/swagger

### First Steps Checklist
- [ ] All services show "Up" status in Docker
- [ ] Dashboard loads without errors
- [ ] TorchSharp Inspector displays system information
- [ ] API health check returns 200 OK
- [ ] Monitoring dashboards accessible

---

## 🌐 Platform Overview

### Service Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │   NanoGPT API   │    │ TorchSharp      │
│   Port: 5169    │    │   Port: 8080    │    │ Inspector       │
│   Web Interface │◄──►│   REST API      │◄──►│ Port: 8082      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │    Grafana      │    │   Docker        │
│   Port: 9090    │    │   Port: 3001    │    │   Containers    │
│   Metrics       │    │   Dashboards    │    │   Management    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **NanoGPT Dashboard** | Main interface for model management | Text generation, training monitoring, configuration |
| **TorchSharp Inspector** | Advanced diagnostic tool | System analysis, model inspection, performance benchmarks |
| **NanoGPT API** | RESTful API for programmatic access | Text generation, model status, training control |
| **Prometheus** | Metrics collection and storage | Performance metrics, system monitoring, alerting |
| **Grafana** | Visualization and monitoring dashboards | Real-time charts, alerts, custom dashboards |

---

## 🎭 NanoGPT Dashboard

### Accessing the Dashboard
Open your browser and navigate to: **http://localhost:5169**

### Main Features

#### 1. Text Generation Interface
- **Location**: Home page, central panel
- **Purpose**: Generate Shakespeare-style text using your trained model
- **How to use**:
  1. Enter a text prompt (e.g., "To be or not to be")
  2. Adjust parameters:
     - **Max Tokens**: Number of tokens to generate (1-500)
     - **Temperature**: Creativity level (0.1-2.0)
  3. Click "Generate Text"
  4. View generated output in the results panel

#### 2. Model Status Monitor
- **Location**: Top navigation bar
- **Purpose**: Real-time model health and performance
- **Information displayed**:
  - Model loading status
  - Current memory usage
  - Last generation timestamp
  - Error status (if any)

#### 3. Training Monitor
- **Location**: Training tab
- **Purpose**: Monitor ongoing training sessions
- **Features**:
  - Real-time loss tracking
  - Training progress percentage
  - Estimated time remaining
  - Training metrics visualization

#### 4. Configuration Panel
- **Location**: Settings tab
- **Purpose**: Adjust model and generation parameters
- **Configurable options**:
  - Default generation length
  - Temperature settings
  - Model checkpoint paths
  - Logging levels

### Dashboard Navigation Tips
- **Home**: Quick text generation and status overview
- **Monitor**: Detailed training and performance metrics
- **Settings**: Configuration and advanced options
- **Help**: Built-in documentation and troubleshooting

---

## 🔍 TorchSharp Inspector

### Accessing the Inspector
Open your browser and navigate to: **http://localhost:8082**

### Main Features

#### 1. System Diagnostics
**Purpose**: Analyze your system's compatibility with TorchSharp and ML workloads

**How to use**:
1. Navigate to "System Diagnostics" section
2. Click "Run Diagnostics"
3. Review results:
   - Hardware specifications
   - TorchSharp compatibility
   - Performance recommendations

**What you'll see**:
```
✅ CPU: Intel i7-1065G7 (4 cores, 8 threads) - Compatible
✅ Memory: 15.78 GB available - Sufficient
⚠️  GPU: Not detected - CPU-only mode
✅ TorchSharp: v0.105.1 - Compatible
```

#### 2. Model Inspection
**Purpose**: Deep analysis of your trained models

**How to use**:
1. Go to "Model Analysis" section
2. Enter model path (e.g., `./model/model.bin`)
3. Select analysis options:
   - Include weight statistics
   - Include bias analysis
   - Generate architecture diagram
4. Click "Analyze Model"

**Analysis Results**:
- Model architecture breakdown
- Parameter count and distribution
- Layer-by-layer analysis
- Compatibility assessment

#### 3. Performance Benchmarks
**Purpose**: Measure model performance and system capabilities

**Benchmark Types**:
- **Inference Speed**: How fast your model generates text
- **Memory Usage**: RAM consumption patterns
- **Throughput**: Requests per second capability
- **Scalability**: Performance with different batch sizes

**How to run benchmarks**:
1. Navigate to "Performance" section
2. Configure benchmark parameters:
   - Model path
   - Number of iterations
   - Batch sizes to test
3. Click "Start Benchmark"
4. Monitor progress and review results

#### 4. Tensor Operations Testing
**Purpose**: Validate TorchSharp functionality and performance

**Available Tests**:
- Tensor creation and manipulation
- Mathematical operations
- Memory management
- Performance under load

#### 5. Memory Analysis
**Purpose**: Monitor and optimize memory usage

**Features**:
- Real-time memory monitoring
- Garbage collection analysis
- Memory leak detection
- Optimization recommendations

#### 6. Report Generation
**Purpose**: Create comprehensive analysis reports

**Report Types**:
- **JSON**: Machine-readable format for automation
- **HTML**: Human-readable web format
- **PDF**: Professional document format

**How to generate reports**:
1. Go to "Reports" section
2. Select report components:
   - System information
   - Model analysis
   - Benchmark results
   - Memory analysis
3. Choose output format
4. Click "Generate Report"
5. Download when ready

---

## 📊 API Usage

### NanoGPT API (Port 8080)

#### Basic Text Generation
```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "To be or not to be",
    "maxTokens": 100,
    "temperature": 0.8
  }'
```

#### Check Model Status
```bash
curl -X GET http://localhost:8080/api/model/status
```

#### Health Check
```bash
curl -X GET http://localhost:8080/health
```

### TorchSharp Inspector API (Port 8082)

#### System Diagnostics
```bash
curl -X GET http://localhost:8082/api/diagnostics/system
```

#### Model Analysis
```bash
curl -X POST http://localhost:8082/api/model/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "checkpointPath": "./model/model.bin",
    "includeWeights": false
  }'
```

#### Run Benchmarks
```bash
curl -X POST http://localhost:8082/api/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{
    "benchmarkTypes": ["inference", "memory"],
    "modelPath": "./model/model.bin",
    "iterations": 50
  }'
```

### API Authentication
Currently running in development mode without authentication. For production use, implement:
- API keys for service access
- Rate limiting for fair usage
- HTTPS for secure communication

---

## 📈 Monitoring & Analytics

### Grafana Dashboards
**Access**: http://localhost:3001  
**Login**: admin / admin123

#### Available Dashboards:

1. **System Overview**
   - CPU and memory usage
   - Service health status
   - Request metrics
   - Error rates

2. **NanoGPT Performance**
   - Text generation latency
   - Throughput metrics
   - Model loading times
   - Cache hit rates

3. **TorchSharp Inspector Metrics**
   - Analysis execution times
   - Benchmark results
   - Memory usage patterns
   - API response times

### Prometheus Metrics
**Access**: http://localhost:9090

**Key Metrics to Monitor**:
- `nanogpt_generation_duration_seconds`: Text generation time
- `inspector_analysis_duration_seconds`: Analysis execution time
- `system_memory_usage_bytes`: Memory consumption
- `http_requests_total`: API request counts
- `service_health_status`: Service availability

### Setting Up Alerts
1. Open Grafana dashboard
2. Navigate to Alerting → Alert Rules
3. Create new rule with conditions:
   - High memory usage (>80%)
   - API errors (>5% error rate)
   - Service downtime (health check failures)
4. Configure notification channels (email, Slack, etc.)

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Service Won't Start
**Symptoms**: Docker containers not running, connection refused errors

**Solutions**:
1. Check Docker is running: `docker --version`
2. Verify ports aren't in use: `netstat -an | findstr :8080`
3. Check service logs: `docker-compose logs [service-name]`
4. Restart services: `docker-compose restart`

#### Model Loading Errors
**Symptoms**: "Model not found" or "Invalid model format" errors

**Solutions**:
1. Verify model file exists and is accessible
2. Check file permissions
3. Validate model format with TorchSharp Inspector
4. Ensure model was trained with compatible version

#### Performance Issues
**Symptoms**: Slow text generation, high memory usage, timeouts

**Solutions**:
1. Run TorchSharp Inspector diagnostics
2. Check system resources with monitoring tools
3. Reduce batch sizes or model complexity
4. Enable garbage collection optimization
5. Consider upgrading hardware

#### API Connection Issues
**Symptoms**: 500 errors, connection timeouts, rate limiting

**Solutions**:
1. Check service health endpoints
2. Verify network connectivity
3. Review API rate limits
4. Check for firewall blocking
5. Examine service logs for errors

### Debug Mode
Enable detailed logging for troubleshooting:

1. **Modify docker-compose.yml**:
   ```yaml
   environment:
     - ASPNETCORE_ENVIRONMENT=Development
     - Logging__LogLevel__Default=Debug
   ```

2. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. **View detailed logs**:
   ```bash
   docker-compose logs -f --tail=100
   ```

### Getting Help
- **Documentation**: Check API_DOCUMENTATION.md
- **Logs**: Review service logs for error details
- **Community**: GitHub Discussions for community support
- **Issues**: GitHub Issues for bug reports

---

## 🎯 Advanced Usage

### Custom Model Training
1. **Prepare your dataset**:
   - Format as plain text file
   - Place in `data/` directory
   - Update configuration

2. **Modify training parameters**:
   ```json
   {
     "ModelConfig": {
       "VocabSize": 65,
       "ContextLength": 256,
       "EmbeddingDim": 384,
       "NumHeads": 6,
       "NumLayers": 6
     },
     "TrainingConfig": {
       "BatchSize": 64,
       "LearningRate": 3e-4,
       "MaxIterations": 5000
     }
   }
   ```

3. **Start training**:
   ```bash
   dotnet run --project NanoGpt.Training
   ```

### Production Deployment
For production environments:

1. **Use production docker-compose file**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Enable HTTPS**:
   - Configure SSL certificates
   - Update service configurations
   - Enable secure headers

3. **Set up monitoring**:
   - Configure alert rules
   - Set up log aggregation
   - Implement health checks

4. **Scale services**:
   ```bash
   docker-compose up -d --scale nanogpt-api=3
   ```

### API Integration
Integrate the platform into your applications:

```python
# Python example
import requests

def generate_text(prompt, max_tokens=100):
    response = requests.post(
        'http://localhost:8080/api/generate',
        json={
            'prompt': prompt,
            'maxTokens': max_tokens,
            'temperature': 0.8
        }
    )
    return response.json()['generatedText']

# Usage
result = generate_text("Once upon a time")
print(result)
```

```javascript
// JavaScript example
async function generateText(prompt, maxTokens = 100) {
    const response = await fetch('http://localhost:8080/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            maxTokens: maxTokens,
            temperature: 0.8
        })
    });
    
    const data = await response.json();
    return data.generatedText;
}

// Usage
generateText("Once upon a time").then(console.log);
```

---

## 💡 Best Practices

### Performance Optimization
1. **Memory Management**:
   - Monitor memory usage regularly
   - Use appropriate batch sizes
   - Enable garbage collection optimization
   - Clear unused model references

2. **Model Optimization**:
   - Use quantization for production models
   - Implement model caching
   - Optimize inference batch sizes
   - Consider model pruning

3. **System Configuration**:
   - Allocate sufficient RAM
   - Use SSD storage for models
   - Optimize Docker resource limits
   - Configure proper logging levels

### Security Best Practices
1. **API Security**:
   - Implement authentication in production
   - Use HTTPS for all communications
   - Set up rate limiting
   - Validate all input parameters

2. **Container Security**:
   - Use official base images
   - Keep dependencies updated
   - Scan for vulnerabilities
   - Limit container privileges

3. **Network Security**:
   - Use internal Docker networks
   - Restrict external access
   - Configure firewalls
   - Monitor network traffic

### Monitoring Best Practices
1. **Key Metrics**:
   - Response times and throughput
   - Error rates and types
   - Resource utilization
   - Model performance metrics

2. **Alerting Strategy**:
   - Set appropriate thresholds
   - Avoid alert fatigue
   - Include actionable information
   - Test alert mechanisms regularly

3. **Log Management**:
   - Centralize log collection
   - Use structured logging
   - Implement log rotation
   - Secure sensitive information

### Development Workflow
1. **Local Development**:
   - Use development configuration
   - Enable hot reload for rapid iteration
   - Use local debugging tools
   - Test with sample data

2. **Testing Strategy**:
   - Write comprehensive unit tests
   - Implement integration tests
   - Test performance under load
   - Validate API contracts

3. **Deployment Pipeline**:
   - Automate build and deployment
   - Use environment-specific configurations
   - Implement health checks
   - Plan rollback strategies

---

## 🎉 Conclusion

Congratulations! You now have a comprehensive understanding of the NanoGPT Complete ML Platform. This platform provides everything you need for:

- 🤖 Training and deploying GPT-style language models
- 🔍 Advanced model analysis and diagnostics
- 📊 Comprehensive monitoring and analytics
- 🌐 Production-ready API services
- 🐳 Containerized deployment and scaling

### Next Steps
1. **Experiment**: Try generating text with different prompts and parameters
2. **Analyze**: Use TorchSharp Inspector to understand your model better
3. **Monitor**: Set up alerts and dashboards for your use case
4. **Integrate**: Connect the APIs to your applications
5. **Scale**: Deploy in production with appropriate security and monitoring

### Resources
- **API Documentation**: Complete API reference with examples
- **GitHub Repository**: Source code and issue tracking
- **Community Forums**: Get help and share experiences
- **Performance Guides**: Optimization tips and best practices

Happy learning and building! 🚀🤖

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Platform**: NanoGPT Complete ML Platform