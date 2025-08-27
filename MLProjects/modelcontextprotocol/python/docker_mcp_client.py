#!/usr/bin/env python3
"""
Docker MCP Stock Server Client
A client to interact with the MCP stock server running in Docker
"""

import subprocess
import json
import sys
import time
from typing import Dict, Any, Optional

class DockerMCPClient:
    def __init__(self, container_name: str = "mcp-stock-server"):
        self.container_name = container_name

    def is_container_running(self) -> bool:
        """Check if the MCP stock server container is running"""
        try:
            result = subprocess.run([
                "docker", "ps", "--filter", f"name={self.container_name}", 
                "--format", "{{.Status}}"
            ], capture_output=True, text=True, timeout=10)
            
            return "Up" in result.stdout
        except:
            return False

    def start_container(self) -> bool:
        """Start the container if not running"""
        try:
            if self.is_container_running():
                print(f"✅ Container {self.container_name} is already running")
                return True
                
            print(f"🚀 Starting container {self.container_name}...")
            result = subprocess.run([
                "docker-compose", "up", "-d"
            ], capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0:
                print(f"✅ Container {self.container_name} started successfully")
                time.sleep(2)  # Give container time to start
                return True
            else:
                print(f"❌ Failed to start container: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error starting container: {e}")
            return False

    def query_stock_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Query a stock tool in the MCP server running in Docker"""
        if not self.is_container_running():
            print(f"❌ Container {self.container_name} is not running")
            return {"error": "Container not running"}

        try:
            # Create the MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            # Execute the request in the container
            cmd = [
                "docker", "exec", "-i", self.container_name,
                "python", "/app/mcp_stock_server.py"
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send initialize request first
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "docker-client", "version": "1.0.0"}
                }
            }

            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.write('{"jsonrpc": "2.0", "method": "notifications/initialized"}\n')
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            process.stdin.close()

            # Read responses
            output, error = process.communicate(timeout=30)
            
            if process.returncode == 0:
                # Parse the last line which should be our tool response
                lines = [line.strip() for line in output.split('\n') if line.strip()]
                if lines:
                    try:
                        response = json.loads(lines[-1])
                        if "result" in response and "content" in response["result"]:
                            content = response["result"]["content"][0]["text"]
                            return json.loads(content)
                    except json.JSONDecodeError:
                        pass
                        
                return {"raw_output": output, "error": error}
            else:
                return {"error": f"Command failed: {error}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "Request timed out"}
        except Exception as e:
            return {"error": f"Exception: {e}"}

    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price"""
        return self.query_stock_tool("get_stock_price", {"symbol": symbol})

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed stock information"""
        return self.query_stock_tool("get_stock_info", {"symbol": symbol})

    def get_stock_history(self, symbol: str, period: str = "1mo") -> Dict[str, Any]:
        """Get stock history"""
        return self.query_stock_tool("get_stock_history", {"symbol": symbol, "period": period})


def main():
    """Main function for command line usage"""
    if len(sys.argv) < 3:
        print("Usage: python docker_mcp_client.py <tool> <symbol> [period]")
        print("Tools: price, info, history")
        print("Example: python docker_mcp_client.py price AAPL")
        sys.exit(1)

    tool = sys.argv[1].lower()
    symbol = sys.argv[2].upper()
    period = sys.argv[3] if len(sys.argv) > 3 else "1mo"

    client = DockerMCPClient()
    
    # Ensure container is running
    if not client.start_container():
        sys.exit(1)

    print(f"\n🔍 Querying Docker MCP server for {symbol}...")
    
    if tool == "price":
        result = client.get_stock_price(symbol)
    elif tool == "info":
        result = client.get_stock_info(symbol)
    elif tool == "history":
        result = client.get_stock_history(symbol, period)
    else:
        print(f"❌ Unknown tool: {tool}")
        sys.exit(1)

    print("\n📊 Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
