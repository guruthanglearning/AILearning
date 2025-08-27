#!/usr/bin/env python3
"""
A simple MCP server for stock price data using yfinance.
This server provides stock quote functionality through the Model Context Protocol.
"""

import asyncio
import json
import sys
import logging
import os
from typing import Any, Sequence
import yfinance as yf
from datetime import datetime, timedelta

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.types as types

# Set up enhanced logging for Docker monitoring
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/mcp_stock_server.log'),
        # Note: Removed stdout handler to avoid interfering with MCP JSON protocol
        # For Docker: logs will be in the log file, use docker exec to view them
    ]
)
logger = logging.getLogger(__name__)

# Log server startup
logger.info("MCP Stock Server starting up...")
logger.info(f"Log directory: {log_dir}")
logger.info("Running locally")

# Create a server instance
server = Server("stock-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        Tool(
            name="get_stock_price",
            description="Get current stock price and basic information for a given ticker symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_stock_info",
            description="Get detailed company information and financial metrics for a given ticker symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)",
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_stock_history",
            description="Get historical stock price data for a given ticker symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)",
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
                        "default": "1mo"
                    }
                },
                "required": ["symbol"],
            },
        ),
    ]



@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """
    Handle tool execution requests with enhanced logging for Docker monitoring.
    """
    # Debug logging to stderr to see if handler is called
    print(f"DEBUG: handle_call_tool called with name={name}, args={arguments}", file=sys.stderr)
    
    # Enhanced request logging for Docker Desktop visibility
    logger.info("FIRE" + "=" * 58 + "FIRE")
    logger.info("INCOMING MCP REQUEST")
    logger.info(f"Tool Requested: {name}")
    logger.info(f"Arguments: {arguments}")
    logger.info(f"Request Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("FIRE" + "=" * 58 + "FIRE")
    
    if not arguments:
        logger.error("ERROR: Missing arguments in request")
        raise ValueError("Missing arguments")
    
    # Log tool usage (original logging)
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "get_stock_price":
        print(f"DEBUG: Processing get_stock_price for symbol: {arguments.get('symbol') if arguments else 'None'}", file=sys.stderr)
        symbol = arguments.get("symbol")
        if not symbol:
            print("DEBUG: Missing symbol argument", file=sys.stderr)
            raise ValueError("Missing symbol argument")
            
        try:
            print(f"DEBUG: Creating yf.Ticker for {symbol}", file=sys.stderr)
            stock = yf.Ticker(symbol.upper())
            print(f"DEBUG: Getting info for {symbol}", file=sys.stderr)
            
            # Add timeout handling for yfinance calls
            import asyncio
            import functools
            
            # Wrap the blocking yfinance calls with timeout
            loop = asyncio.get_event_loop()
            
            try:
                # Get info with timeout
                print(f"DEBUG: Getting stock info with timeout...", file=sys.stderr)
                info = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: stock.info),
                    timeout=10.0
                )
                print(f"DEBUG: Got stock info successfully", file=sys.stderr)
                
                # Get history with timeout
                print(f"DEBUG: Getting stock history with timeout...", file=sys.stderr)
                hist = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: stock.history(period="1d")),
                    timeout=10.0
                )
                print(f"DEBUG: Got stock history successfully", file=sys.stderr)
                
            except asyncio.TimeoutError:
                print(f"DEBUG: Timeout occurred getting data for {symbol}", file=sys.stderr)
                return [types.TextContent(
                    type="text",
                    text=f"Timeout getting data for {symbol}. Please try again later."
                )]
            
            if hist.empty:
                return [types.TextContent(
                    type="text",
                    text=f"No data found for symbol: {symbol}"
                )]
            
            current_price = hist['Close'].iloc[-1]
            previous_close = info.get('previousClose', hist['Close'].iloc[-1])
            change = current_price - previous_close            
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            result = {
                "_mcp_tool_info": {
                    "tool_name": "get_stock_price",
                    "server": "AILearning_StockServer",
                    "data_source": "Custom_YFinance_Server",
                    "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "_tool_attribution": "DATA retrieved using: get_stock_price tool",
                "symbol": symbol.upper(),
                "company_name": info.get('longName', 'N/A'),
                "current_price": round(float(current_price), 2),
                "previous_close": round(float(previous_close), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0,
                "market_cap": int(info.get('marketCap', 0)) if info.get('marketCap') and info.get('marketCap') != 'N/A' else 'N/A',
                "currency": info.get('currency', 'USD'),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Successfully retrieved stock price for {symbol}")
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"Error fetching stock data for {symbol}: {str(e)}"
            )]
    
    elif name == "get_stock_info":
        symbol = arguments.get("symbol")
        if not symbol:
            raise ValueError("Missing symbol argument")
            
        try:
            stock = yf.Ticker(symbol.upper())
            info = stock.info
            
            # Helper function to safely convert values
            def safe_convert(value, convert_func=float, default='N/A'):
                try:
                    if value is None or value == 'N/A':
                        return default
                    return convert_func(value)
                except (ValueError, TypeError):
                    return default
            
            result = {
                "_mcp_tool_info": {
                    "tool_name": "get_stock_info",
                    "server": "AILearning_StockServer",
                    "data_source": "Custom_YFinance_Server",
                    "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "_tool_attribution": "DATA retrieved using: get_stock_info tool",
                "symbol": symbol.upper(),
                "company_name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "market_cap": safe_convert(info.get('marketCap'), int),
                "enterprise_value": safe_convert(info.get('enterpriseValue'), int),
                "pe_ratio": safe_convert(info.get('trailingPE'), float),
                "forward_pe": safe_convert(info.get('forwardPE'), float),
                "price_to_book": safe_convert(info.get('priceToBook'), float),
                "dividend_yield": safe_convert(info.get('dividendYield'), float),
                "beta": safe_convert(info.get('beta'), float),
                "52_week_high": safe_convert(info.get('fiftyTwoWeekHigh'), float),
                "52_week_low": safe_convert(info.get('fiftyTwoWeekLow'), float),
                "average_volume": safe_convert(info.get('averageVolume'), int),
                "website": info.get('website', 'N/A'),
                "business_summary": info.get('longBusinessSummary', 'N/A')[:500] + "..." if info.get('longBusinessSummary') and len(info.get('longBusinessSummary', '')) > 500 else info.get('longBusinessSummary', 'N/A'),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Successfully retrieved stock info for {symbol}")
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"Error fetching stock info for {symbol}: {str(e)}"
            )]
    
    elif name == "get_stock_history":
        symbol = arguments.get("symbol")
        period = arguments.get("period", "1mo")
        
        if not symbol:
            raise ValueError("Missing symbol argument")
            
        try:
            stock = yf.Ticker(symbol.upper())
            hist = stock.history(period=period)
            
            if hist.empty:
                return [types.TextContent(
                    type="text",
                    text=f"No historical data found for symbol: {symbol}"
                )]
            
            # Convert to a list of dictionaries for JSON serialization
            history_data = []
            for date, row in hist.iterrows():
                history_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row['Open']), 2),
                    "high": round(float(row['High']), 2),
                    "low": round(float(row['Low']), 2),
                    "close": round(float(row['Close']), 2),
                    "volume": int(row['Volume'])
                })
            
            result = {
                "_mcp_tool_info": {
                    "tool_name": "get_stock_history",
                    "server": "AILearning_StockServer",
                    "data_source": "Custom_YFinance_Server",
                    "query_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "_tool_attribution": "DATA retrieved using: get_stock_history tool",
                "symbol": symbol.upper(),
                "period": period,
                "data_points": len(history_data),
                "history": history_data[-10:] if len(history_data) > 10 else history_data,  # Return last 10 data points
                "summary": {
                    "start_date": history_data[0]["date"] if history_data else "N/A",
                    "end_date": history_data[-1]["date"] if history_data else "N/A",
                    "highest_price": max([d["high"] for d in history_data]) if history_data else 0,
                    "lowest_price": min([d["low"] for d in history_data]) if history_data else 0,
                    "average_volume": sum([d["volume"] for d in history_data]) / len(history_data) if history_data else 0
                },
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"Successfully retrieved stock history for {symbol} (period: {period})")
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error fetching stock history for {symbol}: {str(e)}")
            return [types.TextContent(
                type="text",
                text=f"Error fetching stock history for {symbol}: {str(e)}"
            )]
    
    else:
        logger.error(f"ERROR: Unknown tool requested: {name}")
        raise ValueError(f"Unknown tool: {name}")

# Add this function to wrap all responses with logging
def log_response(tool_name: str, result: list[types.TextContent]) -> list[types.TextContent]:
    """Log response details for Docker monitoring"""
    response_size = len(str(result))
    logger.info("ROCKET" + "=" * 58 + "ROCKET")
    logger.info("MCP RESPONSE SENT")
    logger.info(f"Tool: {tool_name}")
    logger.info(f"Response Size: {response_size} characters")
    logger.info(f"Status: SUCCESS")
    logger.info(f"Response Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("ROCKET" + "=" * 58 + "ROCKET")
    return result

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="stock-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
