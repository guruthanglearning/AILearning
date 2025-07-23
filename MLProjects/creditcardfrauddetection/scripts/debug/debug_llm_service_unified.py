#!/usr/bin/env python
"""
Unified Debug Script for the LLM Service with Multiple Debug Modes
- Normal mode: Standard console logging and output
- Breakpoint mode: Uses PDB for step-by-step debugging
- VS Code mode: Uses debugpy for visual debugging in VS Code 

Usage:
    python debug_llm_service_unified.py --mode [normal|breakpoint|vscode]
    
Examples:
    # For normal debugging:
    python debug_llm_service_unified.py --mode normal
    
    # For breakpoint debugging:
    python debug_llm_service_unified.py --mode breakpoint
    
    # For VS Code debugging:
    python debug_llm_service_unified.py --mode vscode
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Set up argument parser
parser = argparse.ArgumentParser(description="Debug LLM Service with multiple debug modes")
parser.add_argument("--mode", type=str, choices=["normal", "breakpoint", "vscode"], 
                    default="normal", help="Debug mode: normal, breakpoint, or vscode")
args = parser.parse_args()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Set up VS Code debugging if in vscode mode
if args.mode == "vscode":
    try:
        import debugpy
        # Allow VS Code to attach to this script
        debugpy.listen(5678)
        print("Waiting for VS Code debugger to attach (press F5 in VS Code)...")
        # Uncomment this line if you want the script to wait for the debugger to attach
        # debugpy.wait_for_client()
    except ImportError:
        print("debugpy not found. Install it with: pip install debugpy")
        print("Continuing without debugpy...")

# Set up PDB if in breakpoint mode
if args.mode == "breakpoint":
    import pdb

# Import the LLM service
from app.services.llm_service import LLMService
from langchain.schema import Document
from app.core.config import settings

def main():
    """Main debug function with debug mode support"""
    logger.info(f"Starting LLM Service debug in {args.mode} mode")
    
    # Create LLM service instance
    llm_service = LLMService()
    logger.info("LLM Service instantiated successfully")
    
    # Test basic query
    logger.info("Testing basic query...")
    test_query = "What patterns indicate credit card fraud?"
    
    if args.mode == "breakpoint":
        pdb.set_trace()  # Set a breakpoint for PDB debugging
        
    # Process the test query
    result = llm_service.process_query(test_query)
    logger.info(f"Query result: {result}")
    
    # Test document processing
    logger.info("Testing document processing...")
    test_docs = [
        Document(page_content="Card declined multiple times in different locations within short time period.", 
                 metadata={"source": "fraud_patterns.txt"}),
        Document(page_content="High-value transactions in unusual merchant categories.", 
                 metadata={"source": "fraud_patterns.txt"})
    ]
    
    if args.mode == "breakpoint":
        pdb.set_trace()  # Set another breakpoint for PDB debugging
        
    # Process the test documents
    result = llm_service.process_documents(test_docs)
    logger.info(f"Document processing result: {result}")
    
    logger.info("LLM Service debug complete")

if __name__ == "__main__":
    main()
