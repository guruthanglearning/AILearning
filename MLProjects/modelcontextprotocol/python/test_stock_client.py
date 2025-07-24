#!/usr/bin/env python3
"""
Simple test client for the MCP stock server
"""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

async def test_mcp_stock_server():
    """Test the MCP stock server with sample requests"""
    
    # Start the server process
    server_path = r"D:\Study\AILearning\MLProjects\modelcontextprotocol\python\mcp_stock_server.py"
    python_path = r"D:/Study/AILearning/shared_Environment/Scripts/python.exe"
    
    process = subprocess.Popen(
        [python_path, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Initialize the server
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialization
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Read initialization response
        response = process.stdout.readline()
        print("Initialization response:", response.strip())
        
        # Send initialized notification (required by MCP protocol)
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_notification) + '\n')
        process.stdin.flush()
        
        # List available tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write(json.dumps(list_tools_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        print("Available tools:", response.strip())
        
        # Test get_stock_price tool
        # Get user input for stock symbol
        print("\nAvailable options:")
        print("1. Get stock price")
        print("2. Get stock info")
        print("3. Get stock history")
        print("4. Exit")
        
        option = input("Select an option (1-4): ")

        if option not in ["1", "2","3","4"]:
            print("Invalid option. Exiting.")
            return

        if option == "4":
            print("Exiting.")
            return

        symbol = input("Enter stock symbol (e.g., AAPL): ").upper()
        
        if option == "1":            
            stock_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_stock_price",
                    "arguments": {
                        "symbol": symbol
                    }
                }
            }
        elif option == "2":            
            stock_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_stock_info",
                    "arguments": {
                        "symbol": symbol
                    }
                }
            }
        elif option == "3":
            period = input("Enter period (1d, 5d, 1mo, 3mo, 6mo, 1y, default=1mo): ") or "1mo"
            stock_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_stock_history",
                    "arguments": {
                        "symbol": symbol,
                        "period": period
                    }
                }
            }
        
        print(f"Sending request: {json.dumps(stock_request, indent=2)}")
        
        process.stdin.write(json.dumps(stock_request) + '\n')
        process.stdin.flush()
        
        response = process.stdout.readline()
        print("Stock response:", response.strip())
        
        # Parse and format the response
        try:
            response_data = json.loads(response.strip())
            if "result" in response_data and "content" in response_data["result"]:
                content = response_data["result"]["content"][0]["text"]
                result_json = json.loads(content)
                print("\n📊 Formatted Result:")
                print(json.dumps(result_json, indent=2))
            elif "error" in response_data:
                print(f"❌ Error: {response_data['error']}")
            else:
                print("❌ Unexpected response format")
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
        
    except Exception as e:
        print(f"Error testing server: {e}")
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Server stderr: {stderr_output}")
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_stock_server())
