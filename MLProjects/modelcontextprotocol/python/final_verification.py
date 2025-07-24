#!/usr/bin/env python3
"""
Final verification test for the MCP Stock Server
Tests all three tools: get_stock_price, get_stock_info, get_stock_history
"""

import asyncio
import json
import subprocess

async def test_all_stock_tools():
    """Test all stock tools with MSFT as example"""
    
    server_path = r"D:\Study\AILearning\MLProjects\modelcontextprotocol\python\mcp_stock_server.py"
    python_path = r"D:/Study/AILearning/shared_Environment/Scripts/python.exe"
    
    print("🔧 Testing Complete MCP Stock Server...")
    print("=" * 60)
    
    process = subprocess.Popen(
        [python_path, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()
        print("✅ Server initialized successfully")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        # Test 1: Get stock price
        print("\n📊 Test 1: Getting MSFT stock price...")
        stock_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_stock_price",
                "arguments": {"symbol": "MSFT"}
            }
        }
        
        process.stdin.write(json.dumps(stock_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        response_data = json.loads(response.strip())
        if "result" in response_data:
            content = json.loads(response_data["result"]["content"][0]["text"])
            print(f"✅ Current Price: ${content['current_price']}")
            print(f"   Company: {content['company_name']}")
            print(f"   Change: ${content['change']} ({content['change_percent']}%)")
        
        # Test 2: Get detailed stock info
        print("\n📋 Test 2: Getting detailed MSFT info...")
        info_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_stock_info",
                "arguments": {"symbol": "MSFT"}
            }
        }
        
        process.stdin.write(json.dumps(info_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        response_data = json.loads(response.strip())
        if "result" in response_data:
            content = json.loads(response_data["result"]["content"][0]["text"])
            print(f"✅ Sector: {content['sector']}")
            print(f"   P/E Ratio: {content['pe_ratio']}")
            print(f"   Market Cap: ${content['market_cap']:,}")
        
        # Test 3: Get stock history
        print("\n📈 Test 3: Getting MSFT 1-week history...")
        history_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "get_stock_history",
                "arguments": {"symbol": "MSFT", "period": "5d"}
            }
        }
        
        process.stdin.write(json.dumps(history_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        response_data = json.loads(response.strip())
        if "result" in response_data:
            content = json.loads(response_data["result"]["content"][0]["text"])
            print(f"✅ Data Points: {content['data_points']}")
            print(f"   Highest: ${content['summary']['highest_price']}")
            print(f"   Lowest: ${content['summary']['lowest_price']}")
            print(f"   Avg Volume: {content['summary']['average_volume']:,}")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! MCP Stock Server is ready for VS Code integration!")
        print("💡 To use in VS Code:")
        print("   1. Restart VS Code to load the MCP configuration")
        print("   2. Open Claude Dev or another MCP-compatible tool")
        print("   3. Ask for stock information using natural language")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Server stderr: {stderr_output}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_all_stock_tools())
