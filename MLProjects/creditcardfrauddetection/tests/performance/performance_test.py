#!/usr/bin/env python3
"""
Performance testing script for the fraud detection API.
This script sends a large volume of concurrent requests to test system performance.
"""

import os
import sys
import argparse
import asyncio
import time
import json
import random
import uuid
from datetime import datetime, timedelta
import statistics
import aiohttp

# Configuration
DEFAULT_ENDPOINT = "http://localhost:8000/api/v1/detect-fraud"
DEFAULT_API_KEY = "development_api_key"
DEFAULT_CONCURRENCY = 10
DEFAULT_TOTAL_REQUESTS = 100
DEFAULT_DELAY = 0.1  # seconds between batches

# Merchant categories
MERCHANT_CATEGORIES = [
    "Electronics", "Grocery", "Restaurant", "Travel", "Entertainment",
    "Healthcare", "Retail", "Gas Station", "Online Services", "Luxury Goods"
]

# Countries
COUNTRIES = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "IT", "ES", "BR"]

# Transaction generation
def generate_transaction():
    """Generate a random transaction."""
    # Random amount ($10-$1000)
    amount = round(random.uniform(10.0, 1000.0), 2)
    
    # Random timestamp in last 24 hours
    now = datetime.now()
    random_time = now - timedelta(hours=random.uniform(0, 24))
    timestamp = random_time.isoformat() + "Z"
    
    # Random boolean for is_online
    is_online = random.choice([True, False])
    
    # Random merchant category
    merchant_category = random.choice(MERCHANT_CATEGORIES)
    
    # Random merchant country
    merchant_country = random.choice(COUNTRIES)
    
    # Random merchant name
    merchant_name = f"{merchant_category} Store {random.randint(1, 100)}"
    
    # Random coordinates (approximately North America)
    latitude = random.uniform(25.0, 49.0)
    longitude = random.uniform(-125.0, -70.0)
    
    # Create transaction
    return {
        "transaction_id": f"tx_{uuid.uuid4().hex}",
        "card_id": f"card_{uuid.uuid4().hex[:12]}",
        "merchant_id": f"merch_{random.randint(10000, 99999)}",
        "timestamp": timestamp,
        "amount": amount,
        "merchant_category": merchant_category,
        "merchant_name": merchant_name,
        "merchant_country": merchant_country,
        "merchant_zip": f"{random.randint(10000, 99999)}",
        "customer_id": f"cust_{random.randint(10000, 99999)}",
        "is_online": is_online,
        "device_id": f"dev_{uuid.uuid4().hex[:8]}" if is_online else None,
        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}" if is_online else None,
        "currency": "USD",
        "latitude": latitude,
        "longitude": longitude
    }

# API client
async def send_request(session, url, api_key, transaction):
    """Send a request to the API."""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    start_time = time.time()
    try:
        async with session.post(url, headers=headers, json=transaction) as response:
            status_code = response.status
            try:
                response_data = await response.json()
            except:
                response_data = await response.text()
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # ms
            
            return {
                "status_code": status_code,
                "response": response_data,
                "processing_time": processing_time
            }
    except Exception as e:
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # ms
        
        return {
            "status_code": 0,
            "response": str(e),
            "processing_time": processing_time
        }

# Batch processing
async def process_batch(session, url, api_key, batch_size):
    """Process a batch of requests concurrently."""
    tasks = []
    for _ in range(batch_size):
        transaction = generate_transaction()
        task = send_request(session, url, api_key, transaction)
        tasks.append(task)
    
    return await asyncio.gather(*tasks)

# Main performance test
async def run_performance_test(url, api_key, concurrency, total_requests, delay):
    """Run the performance test."""
    print(f"Starting performance test with {concurrency} concurrent requests")
    print(f"Total requests: {total_requests}")
    print(f"Endpoint: {url}")
    
    # Create session
    async with aiohttp.ClientSession() as session:
        results = []
        batches = (total_requests + concurrency - 1) // concurrency  # Ceiling division
        
        for i in range(batches):
            # Calculate batch size (may be smaller for last batch)
            batch_size = min(concurrency, total_requests - i * concurrency)
            if batch_size <= 0:
                break
            
            print(f"Processing batch {i+1}/{batches} with {batch_size} requests")
            batch_results = await process_batch(session, url, api_key, batch_size)
            results.extend(batch_results)
            
            # Add delay between batches
            if i < batches - 1 and delay > 0:
                await asyncio.sleep(delay)
    
    return results

# Results analysis
def analyze_results(results):
    """Analyze test results."""
    # Overall statistics
    total_requests = len(results)
    successful_requests = sum(1 for r in results if 200 <= r["status_code"] < 300)
    success_rate = successful_requests / total_requests if total_requests > 0 else 0
    
    # Processing times
    processing_times = [r["processing_time"] for r in results]
    avg_processing_time = statistics.mean(processing_times) if processing_times else 0
    min_processing_time = min(processing_times) if processing_times else 0
    max_processing_time = max(processing_times) if processing_times else 0
    
    # Calculate percentiles
    if processing_times:
        # Sort in-place for percentile calculations
        processing_times.sort()
        p50 = processing_times[int(0.5 * len(processing_times))]
        p90 = processing_times[int(0.9 * len(processing_times))]
        p95 = processing_times[int(0.95 * len(processing_times))]
        p99 = processing_times[int(0.99 * len(processing_times))]
    else:
        p50 = p90 = p95 = p99 = 0
    
    # Status code distribution
    status_codes = {}
    for r in results:
        status = r["status_code"]
        status_codes[status] = status_codes.get(status, 0) + 1
    
    # Fraud detection results
    fraud_count = sum(1 for r in results 
                     if 200 <= r["status_code"] < 300 
                     and isinstance(r["response"], dict) 
                     and r["response"].get("is_fraud", False))
    
    fraud_rate = fraud_count / successful_requests if successful_requests > 0 else 0
    
    # Review required count
    review_count = sum(1 for r in results 
                      if 200 <= r["status_code"] < 300 
                      and isinstance(r["response"], dict) 
                      and r["response"].get("requires_review", False))
    
    review_rate = review_count / successful_requests if successful_requests > 0 else 0
    
    # Format results
    results = {
        "summary": {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "avg_processing_time_ms": avg_processing_time,
            "min_processing_time_ms": min_processing_time,
            "max_processing_time_ms": max_processing_time,
            "p50_ms": p50,
            "p90_ms": p90,
            "p95_ms": p95,
            "p99_ms": p99,
            "fraud_count": fraud_count,
            "fraud_rate": fraud_rate,
            "review_count": review_count,
            "review_rate": review_rate
        },
        "status_codes": status_codes
    }
    
    return results

# Main function
async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Performance testing for fraud detection API")
    parser.add_argument("--url", type=str, default=DEFAULT_ENDPOINT,
                        help=f"API endpoint URL (default: {DEFAULT_ENDPOINT})")
    parser.add_argument("--api-key", type=str, default=DEFAULT_API_KEY,
                        help=f"API key for authentication (default: {DEFAULT_API_KEY})")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--total", type=int, default=DEFAULT_TOTAL_REQUESTS,
                        help=f"Total number of requests (default: {DEFAULT_TOTAL_REQUESTS})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                        help=f"Delay between batches in seconds (default: {DEFAULT_DELAY})")
    parser.add_argument("--output", type=str, 
                        help="Output file for detailed results (JSON)")
    args = parser.parse_args()
    
    # Run test
    start_time = time.time()
    results = await run_performance_test(
        args.url, args.api_key, args.concurrency, args.total, args.delay
    )
    end_time = time.time()
    
    # Analyze results
    analysis = analyze_results(results)
    
    # Print summary
    print("\nPerformance Test Results:")
    print("-" * 40)
    print(f"Total requests: {analysis['summary']['total_requests']}")
    print(f"Successful requests: {analysis['summary']['successful_requests']}")
    print(f"Success rate: {analysis['summary']['success_rate'] * 100:.2f}%")
    print(f"Total test time: {end_time - start_time:.2f} seconds")
    print("\nLatency Statistics:")
    print(f"Average processing time: {analysis['summary']['avg_processing_time_ms']:.2f} ms")
    print(f"Min/Max processing time: {analysis['summary']['min_processing_time_ms']:.2f}/{analysis['summary']['max_processing_time_ms']:.2f} ms")
    print(f"P50 (median) latency: {analysis['summary']['p50_ms']:.2f} ms")
    print(f"P90 latency: {analysis['summary']['p90_ms']:.2f} ms")
    print(f"P95 latency: {analysis['summary']['p95_ms']:.2f} ms")
    print(f"P99 latency: {analysis['summary']['p99_ms']:.2f} ms")
    print("\nFraud Statistics:")
    print(f"Fraud count: {analysis['summary']['fraud_count']}")
    print(f"Fraud rate: {analysis['summary']['fraud_rate'] * 100:.2f}%")
    print(f"Review required: {analysis['summary']['review_count']}")
    print(f"Review rate: {analysis['summary']['review_rate'] * 100:.2f}%")
    print("\nStatus Code Distribution:")
    for status, count in sorted(analysis['status_codes'].items()):
        print(f"  {status}: {count} ({count/analysis['summary']['total_requests']*100:.2f}%)")
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            full_results = {
                "analysis": analysis,
                "raw_results": [
                    {
                        "status_code": r["status_code"],
                        "processing_time": r["processing_time"],
                        # Include abbreviated response to keep file size reasonable
                        "response_summary": {
                            "is_fraud": r["response"].get("is_fraud") if isinstance(r["response"], dict) else None,
                            "confidence_score": r["response"].get("confidence_score") if isinstance(r["response"], dict) else None,
                            "requires_review": r["response"].get("requires_review") if isinstance(r["response"], dict) else None,
                        } if 200 <= r["status_code"] < 300 else str(r["response"])[:100]
                    }
                    for r in results
                ],
                "test_config": {
                    "url": args.url,
                    "concurrency": args.concurrency,
                    "total_requests": args.total,
                    "test_start_time": start_time,
                    "test_end_time": end_time,
                    "test_duration": end_time - start_time
                }
            }
            json.dump(full_results, f, indent=2)
            print(f"\nDetailed results saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
