# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Model Context Protocol (MCP) server exposing stock market data (via `yfinance`) as MCP tools, runnable either directly with Python or via Docker. All code lives under `python/`.

## Commands

```powershell
cd D:\Study\AILearning\MLProjects\modelcontextprotocol\python

D:/Study/AILearning/shared_Environment/Scripts/pip.exe install -r requirements.txt
D:/Study/AILearning/shared_Environment/Scripts/python.exe mcp_stock_server.py   # runs the MCP server over stdio (not a normal HTTP server — see below)

# Command-line test client
D:/Study/AILearning/shared_Environment/Scripts/python.exe test_stock_client_args.py --option 1 --symbol AAPL   # price
D:/Study/AILearning/shared_Environment/Scripts/python.exe test_stock_client_args.py --option 2 --symbol AAPL   # company info
D:/Study/AILearning/shared_Environment/Scripts/python.exe test_stock_client_args.py --option 3 --symbol AAPL --period 6mo   # history

# Interactive PowerShell menu (wraps the Python client)
.\run_stock_tests.ps1

# Docker lifecycle (per repo-root policy: local Docker build/run needs no permission ask; only pushing images to a remote registry would)
.\deploy_mcp_stock_docker.ps1 -Action deploy    # build + run
.\deploy_mcp_stock_docker.ps1 -Action status
.\deploy_mcp_stock_docker.ps1 -Action logs
.\deploy_mcp_stock_docker.ps1 -Action rebuild -Force
.\test_docker_mcp_stock.ps1 -AllTests -Verbose  # validates the container end-to-end
```

There is no unit test suite (`pytest`/`black`/`flake8` are mentioned in `README.md`'s "Development Setup" but are not actually configured — no config files, no test files matching that pattern exist). `test_stock_client_args.py` and the `.ps1` scripts are the real validation path: they exercise the running server, not a mocked one.

## Architecture

`mcp_stock_server.py` is a single-file MCP server built on the `mcp` SDK's `Server` class, communicating over stdio (`stdio_server()`), not HTTP — the server is invoked as a subprocess by an MCP client (a `docker exec -i ...` command, VS Code's MCP integration, or `docker_mcp_client.py`), not connected to over a socket.

- `@server.list_tools()` declares 3 tools with JSON-schema input validation: `get_stock_price`, `get_stock_info`, `get_stock_history`.
- `@server.call_tool()` is a single dispatch function with an `if/elif` chain per tool name — new tools need a case added here *and* a corresponding entry in `handle_list_tools()`, or the tool is listed but unreachable (or callable but undiscoverable).
- Every yfinance call in `get_stock_price` is wrapped in `asyncio.wait_for(loop.run_in_executor(...), timeout=10.0)` since `yfinance` is a blocking library; `get_stock_info` and `get_stock_history` currently call it synchronously without that wrapper — if you add timeout handling, match the existing pattern from `get_stock_price`.
- Logging goes only to `logs/mcp_stock_server.log` (`logging.FileHandler`) — stdout is intentionally left free of log output because stdout carries the MCP JSON-RPC protocol; don't add a stdout log handler or you'll corrupt the protocol stream. Debug `print(..., file=sys.stderr)` calls are the sanctioned way to trace execution without touching stdout.
- `docker_mcp_client.py` is the production client (spawns/talks to the server via Docker); `test_stock_client_args.py` is a standalone CLI client for direct scripted testing; both speak the same stdio MCP protocol independently rather than sharing a client library.

## Known doc/code drift

`README.md` documents a 4th tool, `analyze_stock_trend` (with buy/sell recommendations, RSI, moving averages), but it is **not implemented** in `mcp_stock_server.py` — only 3 tools exist. Don't assume it exists; if asked to add it, treat it as new work, not a bug fix.
