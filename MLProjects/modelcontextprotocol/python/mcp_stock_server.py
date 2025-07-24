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

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/mcp_stock_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
    Handle tool execution requests.
    """
    if not arguments:
        raise ValueError("Missing arguments")

    # Log tool usage
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "get_stock_price":
        symbol = arguments.get("symbol")
        if not symbol:
            raise ValueError("Missing symbol argument")
            
        try:
            stock = yf.Ticker(symbol.upper())
            info = stock.info
            hist = stock.history(period="1d")
            
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
                "_tool_attribution": "📊 Data retrieved using: get_stock_price tool",
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
                "_tool_attribution": "📋 Data retrieved using: get_stock_info tool",
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
                "_tool_attribution": "📈 Data retrieved using: get_stock_history tool",
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
        raise ValueError(f"Unknown tool: {name}")

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
