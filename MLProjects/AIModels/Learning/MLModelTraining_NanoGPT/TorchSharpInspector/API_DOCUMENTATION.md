# TorchSharp Inspector API Documentation 🔍

## Overview

The TorchSharp Inspector provides a comprehensive REST API for analyzing .NET machine learning models, system diagnostics, and performance benchmarking. All endpoints return JSON responses and support standard HTTP status codes.

**Base URL**: `http://localhost:8082`  
**API Version**: v1.0  
**Content-Type**: `application/json`

---

## 🏥 Health & Status

### Health Check
Check if the service is running and healthy.

```http
GET /api/health
```

**Response:**
```json
{
  "status": "Healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": "2h 15m 30s"
}
```

---

## 🖥️ System Diagnostics

### Get System Information
Retrieve comprehensive system information including hardware, software, and TorchSharp compatibility.

```http
GET /api/diagnostics/system
```

**Response:**
```json
{
  "hardware": {
    "cpu": {
      "name": "Intel(R) Core(TM) i7-1065G7 CPU @ 1.30GHz",
      "cores": 4,
      "threads": 8,
      "baseClockSpeed": 1.30,
      "maxClockSpeed": 3.90
    },
    "memory": {
      "totalMemoryGB": 15.78,
      "availableMemoryGB": 8.45,
      "usedMemoryGB": 7.33
    },
    "storage": {
      "totalSpaceGB": 256.0,
      "freeSpaceGB": 128.5,
      "usedSpaceGB": 127.5
    }
  },
  "software": {
    "operatingSystem": "Windows 11 Pro",
    "dotNetVersion": "10.0.0",
    "torchSharpVersion": "0.105.1",
    "architecture": "x64"
  },
  "compatibility": {
    "torchSharpSupported": true,
    "gpuAcceleration": false,
    "recommendedForTraining": true,
    "warnings": []
  }
}
```

### Run Hardware Compatibility Test
Perform comprehensive hardware compatibility analysis.

```http
POST /api/diagnostics/compatibility
```

**Response:**
```json
{
  "overallCompatibility": "Compatible",
  "score": 85,
  "tests": [
    {
      "name": "CPU Performance",
      "status": "Passed",
      "score": 90,
      "message": "CPU meets requirements for model training"
    },
    {
      "name": "Memory Capacity",
      "status": "Passed",
      "score": 85,
      "message": "Sufficient RAM for medium-scale models"
    },
    {
      "name": "GPU Acceleration",
      "status": "Not Available",
      "score": 0,
      "message": "No GPU detected, CPU-only mode"
    }
  ],
  "recommendations": [
    "Consider adding GPU for faster training",
    "Increase batch size for better CPU utilization"
  ]
}
```

---

## 🤖 Model Analysis

### Analyze Model Checkpoint
Inspect a model checkpoint file for detailed information.

```http
POST /api/model/analyze
Content-Type: application/json

{
  "checkpointPath": "C:/path/to/model.bin",
  "includeWeights": false,
  "includeBiases": true
}
```

**Response:**
```json
{
  "modelInfo": {
    "fileName": "model.bin",
    "fileSize": "47.2 MB",
    "lastModified": "2024-01-15T08:30:00Z",
    "modelType": "GPT",
    "version": "1.0"
  },
  "architecture": {
    "layers": [
      {
        "name": "embedding",
        "type": "Embedding",
        "parameters": 24960,
        "shape": "[65, 384]"
      },
      {
        "name": "transformer_block_0",
        "type": "TransformerBlock",
        "parameters": 1180416,
        "subLayers": ["multihead_attention", "feed_forward", "layer_norm"]
      }
    ],
    "totalParameters": 10788929,
    "trainableParameters": 10788929
  },
  "statistics": {
    "parameterDistribution": {
      "mean": 0.0023,
      "std": 0.156,
      "min": -0.892,
      "max": 0.847
    },
    "layerSizes": {
      "embedding": "24960 params",
      "transformers": "10.2M params",
      "output": "24960 params"
    }
  }
}
```

### Get Model Architecture
Get detailed model architecture information.

```http
GET /api/model/architecture?modelPath={path}
```

**Parameters:**
- `modelPath` (string, required): Path to the model file

**Response:**
```json
{
  "modelType": "GPT",
  "totalLayers": 6,
  "embeddingDimension": 384,
  "attentionHeads": 6,
  "vocabularySize": 65,
  "contextLength": 256,
  "architecture": [
    {
      "layerIndex": 0,
      "layerType": "Embedding",
      "inputShape": "[batch_size, seq_len]",
      "outputShape": "[batch_size, seq_len, 384]",
      "parameters": 24960
    },
    {
      "layerIndex": 1,
      "layerType": "TransformerBlock",
      "inputShape": "[batch_size, seq_len, 384]",
      "outputShape": "[batch_size, seq_len, 384]",
      "parameters": 1180416
    }
  ]
}
```

---

## ⚡ Performance Benchmarks

### Run Performance Benchmark
Execute comprehensive performance benchmarks.

```http
POST /api/benchmark/run
Content-Type: application/json

{
  "benchmarkTypes": ["inference", "memory", "throughput"],
  "modelPath": "C:/path/to/model.bin",
  "iterations": 100,
  "batchSizes": [1, 8, 16, 32]
}
```

**Response:**
```json
{
  "benchmarkId": "bench_20240115_103000",
  "timestamp": "2024-01-15T10:30:00Z",
  "configuration": {
    "modelPath": "C:/path/to/model.bin",
    "iterations": 100,
    "batchSizes": [1, 8, 16, 32]
  },
  "results": {
    "inference": {
      "averageLatency": "145ms",
      "throughputTokensPerSecond": 892,
      "batchPerformance": [
        {
          "batchSize": 1,
          "latency": "45ms",
          "throughput": 356
        },
        {
          "batchSize": 8,
          "latency": "128ms",
          "throughput": 1024
        }
      ]
    },
    "memory": {
      "baselineMemoryMB": 1.2,
      "peakMemoryMB": 4.8,
      "averageMemoryMB": 3.1,
      "memoryEfficiency": 0.65
    },
    "throughput": {
      "tokensPerSecond": 892,
      "requestsPerSecond": 12.4,
      "cpuUtilization": 0.75,
      "memoryUtilization": 0.45
    }
  },
  "summary": {
    "overallScore": 78,
    "performanceGrade": "B+",
    "recommendations": [
      "Increase batch size for better throughput",
      "Consider model quantization for reduced memory usage"
    ]
  }
}
```

### Get Benchmark History
Retrieve historical benchmark results.

```http
GET /api/benchmark/history?limit=10&offset=0
```

**Response:**
```json
{
  "benchmarks": [
    {
      "id": "bench_20240115_103000",
      "timestamp": "2024-01-15T10:30:00Z",
      "modelPath": "model.bin",
      "overallScore": 78,
      "averageLatency": "145ms"
    }
  ],
  "total": 25,
  "hasMore": true
}
```

---

## 🧮 Tensor Operations

### Test Tensor Operations
Execute tensor operation tests to validate TorchSharp functionality.

```http
POST /api/tensor/test
Content-Type: application/json

{
  "operations": ["creation", "arithmetic", "linear_algebra"],
  "tensorSizes": [[100, 100], [1000, 1000]],
  "iterations": 50
}
```

**Response:**
```json
{
  "testResults": {
    "creation": {
      "passed": true,
      "averageTime": "0.5ms",
      "operations": [
        {
          "operation": "zeros",
          "size": "[100, 100]",
          "time": "0.3ms",
          "success": true
        },
        {
          "operation": "random",
          "size": "[1000, 1000]",
          "time": "2.1ms",
          "success": true
        }
      ]
    },
    "arithmetic": {
      "passed": true,
      "averageTime": "1.2ms",
      "operations": [
        {
          "operation": "addition",
          "size": "[100, 100]",
          "time": "0.8ms",
          "success": true
        },
        {
          "operation": "multiplication",
          "size": "[1000, 1000]",
          "time": "15.6ms",
          "success": true
        }
      ]
    }
  },
  "summary": {
    "totalTests": 12,
    "passed": 12,
    "failed": 0,
    "averagePerformance": "Good"
  }
}
```

### Create Custom Tensor
Create a tensor with specified parameters for testing.

```http
POST /api/tensor/create
Content-Type: application/json

{
  "shape": [32, 128],
  "fillType": "random", // "zeros", "ones", "random", "normal"
  "dtype": "float32",
  "seed": 42
}
```

**Response:**
```json
{
  "tensorId": "tensor_20240115_103015",
  "shape": [32, 128],
  "dtype": "float32",
  "size": 16384,
  "memorySizeMB": 0.0625,
  "statistics": {
    "min": -2.1456,
    "max": 2.0834,
    "mean": 0.0123,
    "std": 0.9876
  }
}
```

---

## 📊 Memory Analysis

### Analyze Memory Usage
Get detailed memory usage analysis.

```http
GET /api/memory/analyze
```

**Response:**
```json
{
  "system": {
    "totalMemoryGB": 15.78,
    "availableMemoryGB": 8.45,
    "usedMemoryGB": 7.33,
    "memoryPressure": "Normal"
  },
  "process": {
    "workingSetMB": 145.2,
    "privateMemoryMB": 132.8,
    "virtualMemoryMB": 2048.0,
    "managedMemoryMB": 89.6
  },
  "torchSharp": {
    "allocatedTensorsMB": 24.8,
    "cachedMemoryMB": 12.4,
    "activeTensors": 156,
    "memoryEfficiency": 0.82
  },
  "recommendations": [
    "Memory usage is within normal limits",
    "Consider garbage collection for better efficiency"
  ]
}
```

### Force Garbage Collection
Trigger garbage collection and return memory statistics.

```http
POST /api/memory/gc
```

**Response:**
```json
{
  "beforeGC": {
    "managedMemoryMB": 89.6,
    "workingSetMB": 145.2
  },
  "afterGC": {
    "managedMemoryMB": 67.3,
    "workingSetMB": 128.9
  },
  "freedMemoryMB": 22.3,
  "gcDuration": "45ms",
  "generation": 2
}
```

---

## 📋 Report Generation

### Generate Analysis Report
Generate a comprehensive analysis report.

```http
POST /api/report/generate
Content-Type: application/json

{
  "includeSystemInfo": true,
  "includeModelAnalysis": true,
  "includeBenchmarks": true,
  "includeMemoryAnalysis": true,
  "modelPath": "C:/path/to/model.bin",
  "format": "json" // "json", "html", "pdf"
}
```

**Response:**
```json
{
  "reportId": "report_20240115_103030",
  "timestamp": "2024-01-15T10:30:30Z",
  "format": "json",
  "sections": {
    "systemInfo": { /* System information data */ },
    "modelAnalysis": { /* Model analysis data */ },
    "benchmarks": { /* Benchmark results */ },
    "memoryAnalysis": { /* Memory usage data */ }
  },
  "summary": {
    "overallHealth": "Good",
    "performanceScore": 78,
    "compatibilityScore": 85,
    "recommendations": [
      "System is well-suited for model training",
      "Consider GPU acceleration for production use"
    ]
  },
  "downloadUrl": "/api/report/download/report_20240115_103030"
}
```

### Download Report
Download a generated report file.

```http
GET /api/report/download/{reportId}
```

**Response:** Binary file download (JSON, HTML, or PDF)

---

## 🔧 Configuration

### Get Current Configuration
Retrieve current service configuration.

```http
GET /api/config
```

**Response:**
```json
{
  "version": "1.0.0",
  "environment": "Production",
  "features": {
    "systemDiagnostics": true,
    "modelAnalysis": true,
    "benchmarking": true,
    "tensorOperations": true,
    "memoryAnalysis": true,
    "reportGeneration": true
  },
  "limits": {
    "maxModelSizeMB": 1000,
    "maxBenchmarkIterations": 1000,
    "maxTensorSizeMB": 100,
    "maxReportSizeMB": 50
  },
  "performance": {
    "enableCaching": true,
    "cacheExpirationMinutes": 30,
    "maxConcurrentBenchmarks": 2
  }
}
```

---

## 🚨 Error Handling

### Standard Error Response Format
All API endpoints return errors in a consistent format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid model path provided",
    "details": "The specified file path does not exist or is not accessible",
    "code": "MODEL_PATH_INVALID",
    "timestamp": "2024-01-15T10:30:00Z",
    "requestId": "req_20240115_103000_abc123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Access denied |
| `404` | Not Found | Resource not found |
| `409` | Conflict | Resource already exists |
| `422` | Unprocessable Entity | Validation failed |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Common Error Types

- **ValidationError**: Invalid input parameters
- **FileNotFoundError**: Model or data file not found
- **MemoryError**: Insufficient memory for operation
- **BenchmarkError**: Benchmark execution failed
- **ModelError**: Model loading or analysis failed
- **SystemError**: System resource access failed

---

## 📈 Rate Limiting

API endpoints are rate-limited to ensure service stability:

- **Standard endpoints**: 100 requests per minute per IP
- **Benchmark endpoints**: 10 requests per minute per IP
- **Report generation**: 5 requests per minute per IP

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

---

## 🔐 Authentication

Currently, the API runs without authentication for development purposes. In production environments, consider implementing:

- **API Keys**: For service-to-service communication
- **JWT Tokens**: For user-based authentication
- **OAuth 2.0**: For third-party integrations

---

## 📝 Examples

### Complete Analysis Workflow

```bash
# 1. Check service health
curl -X GET http://localhost:8082/api/health

# 2. Get system information
curl -X GET http://localhost:8082/api/diagnostics/system

# 3. Analyze model
curl -X POST http://localhost:8082/api/model/analyze \
  -H "Content-Type: application/json" \
  -d '{"checkpointPath": "C:/model.bin", "includeWeights": false}'

# 4. Run benchmarks
curl -X POST http://localhost:8082/api/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{"benchmarkTypes": ["inference"], "modelPath": "C:/model.bin", "iterations": 10}'

# 5. Generate report
curl -X POST http://localhost:8082/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"includeSystemInfo": true, "includeModelAnalysis": true, "format": "json"}'
```

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Support**: [GitHub Issues](https://github.com/your-repo/issues)