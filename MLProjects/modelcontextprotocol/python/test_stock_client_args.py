#!/usr/bin/env python3
"""
Command-line argument test client for the MCP stock server
Usage: python test_stock_client_args.py --option 1 --symbol AAPL [--period 1mo]
"""

import asyncio
import json
import subprocess
import sys
import argparse
from typing import Any, Dict

async def test_mcp_stock_server(option: str, symbol: str, period: str = "1mo"):
    """Test the MCP stock server with provided arguments"""
    
    print()
    print("Executing MCP Stock Server request...")
    print(f"   Option: {option}")
    print(f"   Symbol: {symbol}")
    if option == "3":
        print(f"   Period: {period}")
    print("-" * 50)
    
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
                    "name": "args-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialization
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        
        # Read initialization response with timeout
        try:
            response = await asyncio.wait_for(
                asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                timeout=10.0
            )
            print("Server initialized successfully")
        except asyncio.TimeoutError:
            print("Timeout waiting for server initialization")
            return
        
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
        
        try:
            response = await asyncio.wait_for(
                asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                timeout=10.0
            )
            print("Available tools retrieved")
        except asyncio.TimeoutError:
            print("Timeout waiting for tools list")
            return
        
        # Build request based on option
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
            print(f"Getting stock price for {symbol}...")
            
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
            print(f"Getting stock info for {symbol}...")
            
        elif option == "3":
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
            print(f"Getting stock history for {symbol} (period: {period})...")
            
        else:
            print(f"Invalid option: {option}")
            return
        
        # Send the stock request
        process.stdin.write(json.dumps(stock_request) + '\n')
        process.stdin.flush()
        
        # Read the response with timeout
        try:
            response = await asyncio.wait_for(
                asyncio.create_task(asyncio.to_thread(process.stdout.readline)),
                timeout=30.0
            )
            
            if response:
                result = json.loads(response)
                
                if "result" in result:
                    print()
                    print("Response from MCP Stock Server:")
                    print("-" * 50)
                    
                    content = result["result"]["content"]
                    for item in content:
                        if item["type"] == "text":
                            # Pretty print JSON if it looks like JSON
                            text = item["text"]
                            try:
                                parsed = json.loads(text)
                                print(json.dumps(parsed, indent=2))
                            except:
                                print(text)
                        else:
                            print(f"Content type: {item['type']}")
                            print(item)
                    
                    print("-" * 50)
                    print("Request completed successfully!")
                    
                elif "error" in result:
                    print()
                    print(" Error from server:")
                    print(f"   Code: {result['error']['code']}")
                    print(f"   Message: {result['error']['message']}")
                    
                else:
                    print("Unexpected response format:")
                    print(json.dumps(result, indent=2))
                    
            else:
                print("No response received from server")
                
        except asyncio.TimeoutError:
            print("Timeout waiting for stock data response")
            return
        except json.JSONDecodeError as e:
            print(f"Failed to parse server response: {e}")
            return
            
    except Exception as e:
        print(f"Error communicating with server: {e}")
        
    finally:
        # Clean up
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description='Test MCP Stock Server with command line arguments')
    parser.add_argument('-o', '--option', required=True, choices=['1', '2', '3'], 
                        help='Option: 1=price, 2=info, 3=history')
    parser.add_argument('-s', '--symbol', required=True, 
                        help='Stock symbol (e.g., AAPL, GOOGL, MSFT)')
    parser.add_argument('-p', '--period', default='1mo',
                        choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                        help='Time period for history (default: 1mo)')
    
    args = parser.parse_args()
      # Validate symbol
    if not args.symbol.isalpha() or len(args.symbol) > 5:
        print("Invalid symbol. Please enter 1-5 letters only.")
        sys.exit(1)
    
    # Convert to uppercase
    symbol = args.symbol.upper()
    
    print("MCP Stock Server Command Line Test")
    print("=" * 50)
    
    try:
        asyncio.run(test_mcp_stock_server(args.option, symbol, args.period))
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()