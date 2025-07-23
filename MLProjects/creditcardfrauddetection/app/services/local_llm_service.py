"""
Local and Online LLM service for fraud detection using Ollama.
This module allows using Ollama LLMs (both local and online) as an alternative to OpenAI.
The service tries local Ollama first, then online Ollama API if configured, and finally
falls back to CLI approach if both API options are unavailable.
"""

import logging
import time
import requests
from typing import Dict, List, Any, Optional, Union
import re
import json
import os
from pathlib import Path

from app.api.models import DetailedFraudAnalysis
from app.core.config import settings
from langchain.schema import Document

logger = logging.getLogger(__name__)

class LocalLLMService:
    """Service for interacting with local or online Ollama LLMs for fraud detection.
    
    This service provides a multi-tiered approach to LLM inference with configurable preference:
    
    If prefer_online=True (new default):
    1. First tries the online Ollama API if configured
    2. If online fails, tries the local Ollama API
    3. As a last resort, tries the local Ollama CLI
    4. If all else fails, returns a synthetic response
    
    If prefer_online=False (old behavior):
    1. First tries the local Ollama API
    2. If local fails, tries an online Ollama API service if configured
    3. As a last resort, tries the local Ollama CLI
    4. If all else fails, returns a synthetic response
    
    This ensures maximum reliability with configurable preference between online and local.
    """
    
    def __init__(self, model_name:str = "llama3", prefer_online:bool = True):
        """
        Initialize the local/online LLM service.
        
        Args:
            model_name: Name of the model to use, defaults to "llama3"
            prefer_online: Whether to prefer online Ollama API over local, defaults to True
        """
        self.model_name = model_name
        self.use_online_ollama = settings.USE_ONLINE_OLLAMA
        self.online_api_url = settings.ONLINE_OLLAMA_API_URL
        self.online_api_key = settings.ONLINE_OLLAMA_API_KEY
        self.api_url = settings.LOCAL_LLM_API_URL or "http://localhost:11434/api"
        self.prefer_online = prefer_online
        self.online_available = False
        self.local_available = False
        self.available = self._check_availability()
        
        if self.available:
            logger.info(f"OllamaService initialized with model: {model_name}")
            if self.use_online_ollama and self.online_api_url and self.online_api_key:
                # Use masked API key in logs
                masked_key = getattr(settings, 'MASKED_ONLINE_OLLAMA_API_KEY', None)
                if masked_key:
                    logger.info(f"Online Ollama API configured with URL: {self.online_api_url} and key: {masked_key}")
                else:
                    # Fall back to simple masking if property not available
                    if len(self.online_api_key) > 8:
                        masked = self.online_api_key[:4] + "*" * (len(self.online_api_key) - 8) + self.online_api_key[-4:]
                    else:
                        masked = "****"
                    logger.info(f"Online Ollama API configured with URL: {self.online_api_url} and key: {masked}")
            
            if self.prefer_online:
                logger.info("Using online Ollama API as primary and local Ollama as fallback")
            else:
                logger.info("Using local Ollama as primary and online Ollama API as fallback")
        else:
            logger.warning(f"OllamaService not available. Neither local nor online Ollama services are accessible.")
    
    def _check_availability(self) -> bool:
        """
        Check if either local or online LLM service is available.
        Returns True if at least one service is available based on preference.
        """
        self.local_available = False
        self.online_available = False
        
        # Check order depends on preference
        if self.prefer_online:
            # Check online first, then local
            self._check_online_availability()
            self._check_local_availability()
        else:
            # Check local first, then online
            self._check_local_availability()
            self._check_online_availability()
        
        # Log availability status based on preference
        if self.prefer_online:
            if self.online_available:
                logger.info("Using online Ollama as primary service")
            elif self.local_available:
                logger.info("Online Ollama unavailable, falling back to local")
            else:
                logger.warning("Neither online nor local Ollama services are available")
        else:
            if self.local_available:
                logger.info("Using local Ollama as primary service")
            elif self.online_available:
                logger.info("Local Ollama unavailable, falling back to online")
            else:
                logger.warning("Neither local nor online Ollama services are available")
            
        return self.local_available or self.online_available
        
    def _check_local_availability(self) -> bool:
        """Check if local Ollama service is available."""
        try:
            # Try to list models to check if local Ollama is running
            response = requests.get(f"{self.api_url}/tags", timeout=2)
            if response.status_code == 200:
                logger.info("Local Ollama API is available")
                self.local_available = True
                return True
            else:
                logger.warning(f"Local Ollama API returned status code: {response.status_code}")
        except Exception as e:
            logger.warning(f"Error checking local LLM availability: {str(e)}")
        return False
        
    def _check_online_availability(self) -> bool:
        """Check if online Ollama API is available."""
        if not (self.use_online_ollama and self.online_api_url and self.online_api_key):
            return False
            
        try:
            # Different cloud providers may have different health check endpoints
            # Try a few common patterns
            headers = {"Authorization": f"Bearer {self.online_api_key}"}
            
            # First try /status endpoint (common for many APIs)
            try:
                response = requests.get(f"{self.online_api_url}/status", headers=headers, timeout=5)
                if response.status_code == 200:
                    logger.info("Online Ollama API is available via /status endpoint")
                    self.online_available = True
                    return True
                else:
                    logger.debug(f"Online Ollama API /status returned: {response.status_code}")
                    
                    # Try /health endpoint (alternative common pattern)
                    try:
                        response = requests.get(f"{self.online_api_url}/health", headers=headers, timeout=5)
                        if response.status_code == 200:
                            logger.info("Online Ollama API is available via /health endpoint")
                            self.online_available = True
                            return True
                        else:
                            # Try to list models as a final check
                            try:
                                response = requests.get(f"{self.online_api_url}/models", headers=headers, timeout=5)
                                if response.status_code == 200:
                                    logger.info("Online Ollama API is available via /models endpoint")
                                    self.online_available = True
                                    return True
                                else:
                                    logger.warning(f"All online Ollama API endpoints failed with status code: {response.status_code}")
                            except Exception:
                                logger.debug("Failed to connect to models endpoint")
                    except Exception:
                        logger.debug("Failed to connect to health endpoint")
            except Exception:
                logger.debug("Failed to connect to status endpoint")
            
        except Exception as e:
            logger.warning(f"Error checking online Ollama API availability: {str(e)}")
            
        return False
    
    def _create_prompt(self, transaction_text: str, similar_patterns_text: str) -> str:
        """
        Create a prompt for the local LLM.
        
        Args:
            transaction_text: Text description of the transaction
            similar_patterns_text: Text of similar fraud patterns
            
        Returns:
            Formatted prompt string
        """
        # Using a simplified prompt that focuses on getting the key outputs without a lot of explanatory text
        return f"""You are a fraud detection expert. Based on this transaction and patterns, provide a brief assessment.

TRANSACTION:
{transaction_text}

PATTERNS:
{similar_patterns_text}

Respond with exactly three lines:
Fraud Probability: [0-1]
Confidence: [0-1]
Recommendation: [Approve/Review/Deny]

Then add a brief reason for your decision.
"""
    
    def _format_similar_patterns(self, similar_patterns: List[Document]) -> str:
        """
        Format the similar patterns for inclusion in the prompt.
        
        Args:
            similar_patterns: List of similar fraud pattern documents
            
        Returns:
            Formatted text of similar patterns
        """
        if not similar_patterns:
            return "No similar fraud patterns found."
        
        formatted_text = ""
        for i, doc in enumerate(similar_patterns):
            formatted_text += f"SIMILAR PATTERN {i+1}:\n"
            formatted_text += f"ID: {doc.metadata.get('case_id', 'unknown')}\n"
            formatted_text += f"Type: {doc.metadata.get('fraud_type', 'unknown')}\n"
            formatted_text += doc.page_content
            formatted_text += "\n\n"
        
        return formatted_text
    
    def analyze_transaction(
        self,
        transaction_text: str,
        similar_patterns: List[Document]
    ) -> DetailedFraudAnalysis:
        """
        Analyze a transaction with a local or online LLM.
        
        Args:
            transaction_text: Text description of the transaction
            similar_patterns: Similar fraud patterns retrieved from the vector database
            
        Returns:
            DetailedFraudAnalysis object with the analysis results
        """
        if not self.available and not self.use_online_ollama:
            logger.error("Neither local nor online LLM service is available")
            return self._generate_error_analysis("LLM services are not available")
            
        if not self.available and self.use_online_ollama:
            logger.warning("Local LLM service is not available, will try online Ollama API")
        
        start_time = time.time()
        logger.info(f"Analyzing transaction with local LLM model: {self.model_name}")
        
        # Format the similar patterns text
        similar_patterns_text = self._format_similar_patterns(similar_patterns)
        
        # Create the prompt
        prompt = self._create_prompt(transaction_text, similar_patterns_text)
        
        try:
            # Call the local LLM API
            response = self._call_ollama_api(prompt)
            
            # Parse the result
            analysis = self._parse_llm_response(response)
            
            # Add the full analysis text
            analysis.full_analysis = response
            
            # Add the retrieved patterns for reference
            pattern_ids = [doc.metadata.get("case_id", "unknown") for doc in similar_patterns]
            analysis.retrieved_patterns = pattern_ids
            
            logger.info(f"Local LLM analysis completed in {time.time() - start_time:.2f} seconds")
            return analysis
            
        except Exception as e:
            logger.error(f"Error during local LLM analysis: {str(e)}")
            return self._generate_error_analysis(str(e))
    
    def _call_ollama_api(self, prompt: str) -> str:
        """
        Call the Ollama API to generate a response.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response as a string
        """
        try:
            # Determine which approach to try first based on preference setting
            if self.prefer_online and self.use_online_ollama and self.online_available:
                # Try online first, then fall back to local if needed
                online_response = self._try_online_ollama_api(prompt)
                if online_response:
                    return online_response
                    
                # If online failed but local is available, try local
                if self.local_available:
                    logger.warning("Online API approach failed, trying local Ollama API")
                    local_response = self._try_local_ollama_api(prompt)
                    if local_response:
                        return local_response
            else:
                # Try local first, then fall back to online if needed
                if self.local_available:
                    local_response = self._try_local_ollama_api(prompt)
                    if local_response:
                        return local_response
                
                # If local failed but online is available, try online
                if self.use_online_ollama and self.online_available:
                    logger.warning("Local API approach failed, trying online Ollama API")
                    online_response = self._try_online_ollama_api(prompt)
                    if online_response:
                        return online_response
            
            # If we've made it here, both API approaches have failed
            # Now try CLI approach as final fallback
            logger.warning("Both API approaches failed, trying CLI as fallback")
            
            # Fallback to CLI approach
            import subprocess
            import tempfile
            
            # Create a temporary file for the prompt with UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as temp:
                temp.write(prompt)
                temp_path = temp.name
            
            try:
                # Read the prompt from the file with UTF-8 encoding
                with open(temp_path, 'r', encoding='utf-8') as file:
                    prompt_text = file.read()
                
                # Run ollama CLI with the prompt directly
                result = subprocess.run(
                    ["ollama", "run", self.model_name], 
                    input=prompt_text,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',  # Explicitly use UTF-8 encoding
                    timeout=30  # 30 second timeout for CLI
                )
                
                # Clean up the temp file
                os.unlink(temp_path)
                
                if result.returncode == 0:
                    # Ensure we have valid UTF-8 text output
                    logger.info("Successfully used Ollama CLI")
                    return result.stdout
                else:
                    error_msg = f"Ollama CLI error: {result.stderr}"
                    logger.error(error_msg)
                    return f"Error: {error_msg}"
            except (subprocess.TimeoutExpired, UnicodeDecodeError) as e:
                # Clean up the temp file
                os.unlink(temp_path)
                if isinstance(e, subprocess.TimeoutExpired):
                    logger.error("Ollama CLI request timed out")
                else:
                    logger.error(f"Unicode decode error during CLI subprocess: {str(e)}")
                
                # Fall back to a synthetic response that matches our format
                return """Fraud Probability: 0.5
Confidence: 0.5
Recommendation: Review

Unable to complete full analysis due to time constraints. Please review this transaction manually."""
            except Exception as cli_error:
                # Clean up the temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                logger.error(f"Error using Ollama CLI: {str(cli_error)}")
                return f"Error: {str(cli_error)}"
            
            # Try online Ollama API if enabled
            if self.use_online_ollama and self.online_api_url and self.online_api_key:
                try:
                    logger.info(f"Attempting to use online Ollama API at {self.online_api_url}")
                    
                    # Determine API endpoint structure based on URL pattern
                    api_endpoint = f"{self.online_api_url}/generate"
                    if "ollama.cloud" in self.online_api_url:
                        # Ollama Cloud API format
                        payload = {
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.01,
                                "num_predict": 200
                            }
                        }
                    elif "ollama.ai" in self.online_api_url:
                        # Ollama.ai hosted API format
                        payload = {
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.01
                            }
                        }
                    else:
                        # Generic Ollama API format (most compatible)
                        payload = {
                            "model": self.model_name,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.01,
                                "num_predict": 200,
                                "num_ctx": 2048
                            }
                        }
                    
                    # Set up headers with authorization
                    headers = {
                        "Authorization": f"Bearer {self.online_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Make the request to online Ollama API
                    logger.debug(f"Sending request to {api_endpoint}")
                    response = requests.post(
                        api_endpoint, 
                        json=payload,
                        headers=headers,
                        timeout=30  # Give online API more time (cloud services might be slower)
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info("Successfully used online Ollama API")
                        
                        # Handle different response formats from different providers
                        if "response" in result:
                            return result["response"]
                        elif "output" in result:
                            return result["output"]
                        elif "completion" in result:
                            return result["completion"]
                        elif "generated_text" in result:
                            return result["generated_text"]
                        else:
                            logger.warning(f"Unknown response format: {result.keys()}")
                            # Try to return any text field we can find
                            for key, value in result.items():
                                if isinstance(value, str) and len(value) > 10:
                                    return value
                            return str(result)
                    else:
                        # Log detailed error info for debugging
                        logger.warning(f"Online Ollama API returned error: {response.status_code}")
                        logger.debug(f"Error details: {response.text[:500]}...")  # Log first 500 chars of error
                        
                        # Try alternate endpoint if standard endpoint failed
                        if "/generate" in api_endpoint:
                            try:
                                logger.info("Trying alternate endpoint /completions")
                                alt_endpoint = api_endpoint.replace("/generate", "/completions")
                                alt_response = requests.post(
                                    alt_endpoint, 
                                    json=payload,
                                    headers=headers,
                                    timeout=30
                                )
                                
                                if alt_response.status_code == 200:
                                    alt_result = alt_response.json()
                                    logger.info("Successfully used alternate online Ollama API endpoint")
                                    if "choices" in alt_result and len(alt_result["choices"]) > 0:
                                        return alt_result["choices"][0].get("text", "")
                                    return str(alt_result)
                            except Exception as alt_error:
                                logger.warning(f"Alternative endpoint failed: {str(alt_error)}")
                except Exception as online_error:
                    logger.warning(f"Online Ollama API approach failed: {str(online_error)}, trying CLI as fallback")
            else:
                logger.warning("Online Ollama API not configured, skipping to CLI approach")
            
            # Fallback to CLI approach
            import subprocess
            import tempfile
            
            # Create a temporary file for the prompt with UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.txt') as temp:
                temp.write(prompt)
                temp_path = temp.name
            
            try:
                # Read the prompt from the file with UTF-8 encoding
                with open(temp_path, 'r', encoding='utf-8') as file:
                    prompt_text = file.read()
                
                # Run ollama CLI with the prompt directly
                result = subprocess.run(
                    ["ollama", "run", self.model_name], 
                    input=prompt_text,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',  # Explicitly use UTF-8 encoding
                    timeout=30  # 30 second timeout for CLI
                )
                
                # Clean up the temp file
                os.unlink(temp_path)
                
                if result.returncode == 0:
                    # Ensure we have valid UTF-8 text output
                    return result.stdout
                else:
                    error_msg = f"Ollama CLI error: {result.stderr}"
                    logger.error(error_msg)
                    return f"Error: {error_msg}"
            except (subprocess.TimeoutExpired, UnicodeDecodeError) as e:
                # Clean up the temp file
                os.unlink(temp_path)
                if isinstance(e, subprocess.TimeoutExpired):
                    logger.error("Ollama CLI request timed out")
                else:
                    logger.error(f"Unicode decode error during CLI subprocess: {str(e)}")
                
                # Fall back to a synthetic response that matches our format
                return """Fraud Probability: 0.5
Confidence: 0.5
Recommendation: Review

Unable to complete full analysis due to time constraints. Please review this transaction manually."""
            except Exception as cli_error:
                # Clean up the temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                logger.error(f"Error using Ollama CLI: {str(cli_error)}")
                return f"Error: {str(cli_error)}"
                
        except Exception as e:
            logger.error(f"Error in Ollama call: {str(e)}")
            return f"Error: {str(e)}"
    
    def _parse_llm_response(self, response: str) -> DetailedFraudAnalysis:
        """
        Parse the LLM response to extract structured information.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            DetailedFraudAnalysis object with parsed information
        """
        if response.startswith("Error:"):
            # Handle error responses
            return DetailedFraudAnalysis(
                fraud_probability=0.5,
                confidence=0.1,
                reasoning=response,
                recommendation="Review",
                full_analysis=response,
                retrieved_patterns=[]
            )
        
        lines = response.split('\n')
        
        fraud_probability = 0.5  # Default value
        confidence = 0.5  # Default value
        reasoning = ""  # Will collect non-matched lines
        recommendation = "Review"  # Default value
        
        # Parse the response to extract structured information
        non_matched_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "Fraud Probability:" in line or "probability:" in line.lower() or "fraud:" in line.lower():
                try:
                    # Extract the number part
                    prob_text = line.split(':', 1)[1].strip()
                    # Remove any non-numeric characters except for decimal point
                    prob_text = ''.join(c for c in prob_text if c.isdigit() or c == '.')
                    if prob_text:
                        prob = float(prob_text)
                        # If it's a percentage, convert to decimal
                        if prob > 1:
                            prob /= 100
                        fraud_probability = prob
                except Exception as e:
                    logger.warning(f"Error parsing fraud probability: {str(e)}")
            
            elif "Confidence:" in line or "confidence level:" in line.lower():
                try:
                    # Extract the number part
                    conf_text = line.split(':', 1)[1].strip()
                    # Remove any non-numeric characters except for decimal point
                    conf_text = ''.join(c for c in conf_text if c.isdigit() or c == '.')
                    if conf_text:
                        conf = float(conf_text)
                        # If it's a percentage, convert to decimal
                        if conf > 1:
                            conf /= 100
                        confidence = conf
                except Exception as e:
                    logger.warning(f"Error parsing confidence: {str(e)}")
            
            elif "Recommendation:" in line or "decision:" in line.lower():
                # Get the recommendation
                rec = line.split(':', 1)[1].strip().lower()
                if "approve" in rec or "legitimate" in rec or "accept" in rec:
                    recommendation = "Approve"
                elif "deny" in rec or "decline" in rec or "reject" in rec or "fraud" in rec:
                    recommendation = "Deny"
                else:
                    recommendation = "Review"
            
            elif "Reasoning:" in line or "reason:" in line.lower() or "analysis:" in line.lower():
                # Get the rest of the line after the colon
                reason_part = line.split(':', 1)[1].strip() if ':' in line else ""
                if reason_part:
                    non_matched_lines.append(reason_part)
            else:
                # Collect lines that don't match any pattern for reasoning
                non_matched_lines.append(line)
        
        # If no specific reasoning was found, use the collected non-matched lines
        if not reasoning and non_matched_lines:
            reasoning = " ".join(non_matched_lines)
        
        # If still no reasoning, use a default
        if not reasoning:
            reasoning = "Analysis inconclusive"
        
        # Create and return the detailed analysis
        return DetailedFraudAnalysis(
            fraud_probability=fraud_probability,
            confidence=confidence,
            reasoning=reasoning,
            recommendation=recommendation,
            full_analysis=response,
            retrieved_patterns=[]  # Will be filled later
        )
    
    def _generate_error_analysis(self, error_message: str) -> DetailedFraudAnalysis:
        """
        Generate an error analysis when the local LLM fails.
        
        Args:
            error_message: The error message
            
        Returns:
            DetailedFraudAnalysis object with error information
        """
        return DetailedFraudAnalysis(
            fraud_probability=0.5,
            confidence=0.1,
            reasoning=f"Error during analysis: {error_message}. The system encountered an issue while processing this transaction.",
            recommendation="Review",
            full_analysis=f"Error: {error_message}",
            retrieved_patterns=[]
        )
    
    def _try_local_ollama_api(self, prompt: str) -> str:
        """Try to call the local Ollama API."""
        try:
            # Build request to local Ollama API
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.01,  # Very low temperature for more deterministic responses
                    "num_predict": 200,   # Reduced response length limit
                    "num_ctx": 2048       # Reduced context size
                }
            }
            
            # Make the request to local Ollama
            response = requests.post(
                f"{self.api_url}/generate", 
                json=payload,
                timeout=15  # 15 second timeout - fail quickly if API route isn't responsive
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Successfully used local Ollama API")
                return result.get('response', '')
            else:
                logger.warning(f"Local Ollama API returned status code: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.warning("Local API approach timed out")
            return None
        except Exception as api_error:
            logger.warning(f"Local API approach failed: {str(api_error)}")
            return None

    def _try_online_ollama_api(self, prompt: str) -> str:
        """Try to call the online Ollama API."""
        if not (self.use_online_ollama and self.online_api_url and self.online_api_key):
            return None
            
        try:
            logger.info(f"Attempting to use online Ollama API at {self.online_api_url}")
            
            # Determine API endpoint structure based on URL pattern
            api_endpoint = f"{self.online_api_url}/generate"
            if "ollama.cloud" in self.online_api_url:
                # Ollama Cloud API format
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.01,
                        "num_predict": 200
                    }
                }
            elif "ollama.ai" in self.online_api_url:
                # Ollama.ai hosted API format
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.01
                    }
                }
            else:
                # Generic Ollama API format (most compatible)
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.01,
                        "num_predict": 200,
                        "num_ctx": 2048
                    }
                }
            
            # Set up headers with authorization
            headers = {
                "Authorization": f"Bearer {self.online_api_key}",
                "Content-Type": "application/json"
            }
            
            # Make the request to online Ollama API
            logger.debug(f"Sending request to {api_endpoint}")
            response = requests.post(
                api_endpoint, 
                json=payload,
                headers=headers,
                timeout=30  # Give online API more time
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Successfully used online Ollama API")
                
                # Handle different response formats from different providers
                if "response" in result:
                    return result["response"]
                elif "output" in result:
                    return result["output"]
                elif "completion" in result:
                    return result["completion"]
                elif "generated_text" in result:
                    return result["generated_text"]
                else:
                    logger.warning(f"Unknown response format: {result.keys()}")
                    # Try to return any text field we can find
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) > 10:
                            return value
                    return str(result)
            else:
                # Log detailed error info for debugging
                logger.warning(f"Online Ollama API returned error: {response.status_code}")
                logger.debug(f"Error details: {response.text[:500]}...")  # Log first 500 chars of error
                
                # Try alternate endpoint if standard endpoint failed
                if "/generate" in api_endpoint:
                    try:
                        logger.info("Trying alternate endpoint /completions")
                        alt_endpoint = api_endpoint.replace("/generate", "/completions")
                        alt_response = requests.post(
                            alt_endpoint, 
                            json=payload,
                            headers=headers,
                            timeout=30
                        )
                        
                        if alt_response.status_code == 200:
                            alt_result = alt_response.json()
                            logger.info("Successfully used alternate online Ollama API endpoint")
                            if "choices" in alt_result and len(alt_result["choices"]) > 0:
                                return alt_result["choices"][0].get("text", "")
                            return str(alt_result)
                    except Exception as alt_error:
                        logger.warning(f"Alternative endpoint failed: {str(alt_error)}")
                return None
        except Exception as online_error:
            logger.warning(f"Online Ollama API approach failed: {str(online_error)}")
            return None
