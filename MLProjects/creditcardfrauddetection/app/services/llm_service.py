"""
LLM service for advanced fraud detection using Retrieval Augmented Generation.
This module handles interaction with the language model and RAG system.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema import Document
import torch

from app.api.models import Transaction, DetailedFraudAnalysis
from app.core.config import settings
from app.services.enhanced_mock_llm import EnhancedMockLLM, EnhancedFakeListLLM
from app.services.local_llm_service import LocalLLMService

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLMs for fraud detection."""
    def __init__(self):
        """Initialize the LLM service."""
        self.llm = None
        self.embedding_model = None
        self.llm_service_type = None  # Tracks which LLM service type is active
        self.local_llm_service = None  # Will hold LocalLLMService instance if used
        self.enhanced_mock = None  # Will hold EnhancedMockLLM instance if used
        self.initialize_models()
    def initialize_models(self):
        """Initialize the LLM and embedding models."""
        try:
            logger.info("Initializing LLM and embedding models...")
            
            # Initialize the embedding model
            try:
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
                )
                logger.info(f"Initialized embedding model: {settings.EMBEDDING_MODEL}")
            except Exception as emb_error:
                logger.error(f"Error initializing embedding model: {str(emb_error)}")
                logger.info("Falling back to simpler embedding model")
                try:
                    self.embedding_model = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                except Exception as fallback_error:
                    logger.error(f"Failed to initialize fallback embedding model: {str(fallback_error)}")
                    # Continue without embeddings - some functionalities will be limited
            
            # First, check if we should prioritize local LLM regardless of OpenAI availability
            try:
                if hasattr(settings, 'FORCE_LOCAL_LLM') and settings.FORCE_LOCAL_LLM:
                    logger.info("Forcing use of local LLM as configured in settings")
                    self._initialize_mock_llm()
                    return
            except Exception:
                # If setting doesn't exist or there's an error, continue with normal flow
                pass
                
            # Check if OpenAI API key is valid
            api_key = settings.OPENAI_API_KEY
            is_valid_key = api_key and not api_key.startswith(("your_", "sk-your", "sk_test")) and len(api_key) > 20
            
            # Additional check for format - should start with "sk-" or "sk-proj-"
            if is_valid_key and not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
                logger.warning("OpenAI API key doesn't have the expected format (should start with 'sk-' or 'sk-proj-')")
                is_valid_key = False
            
            if not is_valid_key:
                logger.warning("Invalid or missing OpenAI API key. Using alternative LLM approach.")
                self._initialize_mock_llm()
            else:
                # Initialize the LLM with OpenAI
                try:
                    logger.info("Attempting to initialize OpenAI LLM...")
                    self.llm = ChatOpenAI(
                        model_name=settings.LLM_MODEL,
                        temperature=0,
                        openai_api_key=api_key
                    )
                    self.llm_service_type = "openai"
                    
                    # Try a simple test call to verify API key works
                    try:
                        from langchain.schema.messages import HumanMessage
                        test_response = self.llm.invoke([HumanMessage(content="Test")])
                        logger.info(f"Successfully tested LLM connection with model: {settings.LLM_MODEL}")
                    except Exception as test_error:
                        logger.error(f"API key validation failed: {str(test_error)}")
                        logger.warning("Falling back to alternative LLM approach")
                        self._initialize_mock_llm()
                except Exception as llm_error:
                    logger.error(f"Error initializing OpenAI LLM: {str(llm_error)}")
                    logger.warning("Falling back to alternative LLM approach")
                    self._initialize_mock_llm()
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            logger.warning("Service will run with limited functionality")
            # Don't raise the exception - allow the service to start with limited functionality
    def analyze_transaction(
        self,
        transaction_text: str,
        similar_patterns: List[Document]
    ) -> DetailedFraudAnalysis:
        """
        Analyze a transaction with the LLM using RAG.
        
        Args:
            transaction_text: Text description of the transaction
            similar_patterns: Similar fraud patterns retrieved from the vector database
            
        Returns:
            DetailedFraudAnalysis object with the analysis results
        """
        start_time = time.time()
        logger.info(f"Analyzing transaction with LLM service type: {self.llm_service_type}")
        
        # If using local LLM, delegate to that service
        if self.llm_service_type == "local" and self.local_llm_service:
            try:
                logger.info("Using local LLM service for analysis")
                return self.local_llm_service.analyze_transaction(transaction_text, similar_patterns)
            except Exception as e:
                logger.error(f"Local LLM analysis failed: {str(e)}")
                logger.warning("Falling back to other analysis methods")
                # Continue with standard processing if local LLM fails
        
        # If using enhanced mock LLM, use that implementation
        if self.llm_service_type == "enhanced_mock" and self.enhanced_mock:
            try:
                logger.info("Using enhanced mock LLM for analysis")
                return self.enhanced_mock.analyze_transaction(transaction_text, similar_patterns)
            except Exception as e:
                logger.error(f"Enhanced mock LLM analysis failed: {str(e)}")
                logger.warning("Falling back to basic LLM processing")
                # Continue with standard processing if enhanced mock fails
        
        # Format the similar patterns text
        similar_patterns_text = self._format_similar_patterns(similar_patterns)
        
        # Create the prompt
        prompt_template = """
        You are an expert fraud detection analyst specialized in credit card transactions.
        Analyze the following transaction in detail and determine if it is likely fraudulent.
        
        TRANSACTION:
        {transaction_text}
        
        HISTORICAL FRAUD PATTERNS:
        {similar_patterns_text}
        
        Based on the transaction details and historical fraud patterns, evaluate:
        1. How closely does this transaction match known fraud patterns?
        2. What specific indicators suggest this might be fraudulent or legitimate?
        3. Are there any unusual aspects of this transaction that warrant further investigation?
        
        Then provide your assessment with the following structure:
        - Fraud Probability: [a number between 0 and 1]
        - Confidence: [a number between 0 and 1]
        - Reasoning: [detailed explanation of your assessment]
        - Recommendation: [Approve, Deny, or Review]
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["transaction_text", "similar_patterns_text"]
        )
        
        # Create the chain
        chain = prompt | self.llm
        
        # Execute the chain
        try:
            result = chain.invoke({
                "transaction_text": transaction_text,
                "similar_patterns_text": similar_patterns_text
            })
            
            # Parse the result
            analysis = self._parse_llm_response(result.content)
            
            # Add the full analysis text
            analysis.full_analysis = result.content
              # Add the retrieved patterns for reference
            pattern_ids = [doc.metadata.get("case_id", "unknown") for doc in similar_patterns]
            analysis.retrieved_patterns = pattern_ids
            
            logger.info(f"LLM analysis completed in {time.time() - start_time:.2f} seconds")
            return analysis
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error during LLM analysis: {error_msg}")
              # Check if this is a quota error from OpenAI
            if "quota" in error_msg.lower() or "rate limit" in error_msg.lower() or "429" in error_msg or "insufficient_quota" in error_msg:
                logger.warning("Detected OpenAI quota exceeded error, attempting to use fallback systems")
                
                # Try to use online Ollama first, then local if that fails
                try:
                    if self.llm_service_type == "openai":
                        # Initialize Ollama LLM with preference for online API
                        ollama_service = LocalLLMService(model_name=settings.LOCAL_LLM_MODEL, prefer_online=True)                        # Check if online Ollama is available
                        if settings.USE_ONLINE_OLLAMA and ollama_service.online_available:
                            logger.info(f"Successfully switched to online Ollama API due to OpenAI quota limit")
                            self.llm_service_type = "local"  # Still use "local" service type for all Ollama
                            self.local_llm_service = ollama_service
                            
                            # Store the model switching event in session state
                            try:
                                import streamlit as st
                                if 'model_switch_notification' not in st.session_state:
                                    st.session_state['model_switch_notification'] = {
                                        'timestamp': datetime.now().isoformat(),
                                        'message': 'Switched to online Ollama API due to OpenAI quota limit',
                                        'from_model': 'OpenAI',
                                        'to_model': 'Online ' + settings.LOCAL_LLM_MODEL,
                                        'displayed': False
                                    }
                            except ImportError:
                                # Streamlit may not be available in all contexts
                                pass
                            
                            # Retry with online Ollama
                            return self.local_llm_service.analyze_transaction(transaction_text, similar_patterns)
                        
                        # If online Ollama is not available, try local Ollama
                        elif ollama_service.local_available:
                            logger.info(f"Online Ollama not available, switched to local LLM due to OpenAI quota limit")
                            self.llm_service_type = "local"
                            self.local_llm_service = ollama_service
                            
                            # Store the model switching event in session state
                            try:
                                import streamlit as st
                                if 'model_switch_notification' not in st.session_state:
                                    st.session_state['model_switch_notification'] = {
                                        'timestamp': datetime.now().isoformat(),
                                        'message': 'Switched to local LLM due to OpenAI quota limit',
                                        'from_model': 'OpenAI',
                                        'to_model': 'Local ' + settings.LOCAL_LLM_MODEL,
                                        'displayed': False
                                    }
                            except ImportError:
                                # Streamlit may not be available in all contexts
                                pass
                            
                            # Retry with local LLM
                            return self.local_llm_service.analyze_transaction(transaction_text, similar_patterns)
                        else:
                            logger.warning("Neither online nor local Ollama available, using enhanced mock LLM")
                            # Initialize enhanced mock LLM if not already initialized
                            if not self.enhanced_mock:
                                self.enhanced_mock = EnhancedMockLLM()
                            self.llm_service_type = "enhanced_mock"
                            
                            # Store the model switching event
                            try:
                                import streamlit as st
                                if 'model_switch_notification' not in st.session_state:
                                    st.session_state['model_switch_notification'] = {
                                        'timestamp': datetime.now().isoformat(),
                                        'message': 'Switched to mock LLM due to OpenAI quota limit',
                                        'from_model': 'OpenAI',
                                        'to_model': 'Enhanced Mock LLM',
                                        'displayed': False
                                    }
                            except ImportError:
                                pass
                                
                            return self.enhanced_mock.analyze_transaction(transaction_text, similar_patterns)
                except Exception as local_err:
                    logger.error(f"Failed to switch to local LLM after quota error: {str(local_err)}")
            
            # Return a default analysis in case of error
            return DetailedFraudAnalysis(
                fraud_probability=0.5,
                confidence=0.1,
                reasoning="Error during analysis. The system encountered an issue while processing this transaction.",
                recommendation="Review",
                full_analysis=f"Error: {str(e)}",
                retrieved_patterns=[]
            )
    
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
    
    def _parse_llm_response(self, response: str) -> DetailedFraudAnalysis:
        """
        Parse the LLM response to extract structured information.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            DetailedFraudAnalysis object with parsed information
        """
        lines = response.split('\n')
        
        fraud_probability = 0.5  # Default value
        confidence = 0.5  # Default value
        reasoning = "Analysis inconclusive"  # Default value
        recommendation = "Review"  # Default value
        
        # Parse the response to extract structured information
        for line in lines:
            line = line.strip()
            if "Fraud Probability:" in line:
                try:
                    # Handle different formats of probability (0.7, 70%, etc.)
                    prob_text = line.split(':', 1)[1].strip()
                    # Remove any non-numeric characters except for decimal point
                    prob_text = ''.join(c for c in prob_text if c.isdigit() or c == '.')
                    prob = float(prob_text)
                    # If it's a percentage, convert to decimal
                    if prob > 1:
                        prob /= 100
                    fraud_probability = prob
                except Exception as e:
                    logger.warning(f"Error parsing fraud probability: {str(e)}")
            
            elif "Confidence:" in line:
                try:
                    # Handle different formats of confidence (0.7, 70%, etc.)
                    conf_text = line.split(':', 1)[1].strip()
                    # Remove any non-numeric characters except for decimal point
                    conf_text = ''.join(c for c in conf_text if c.isdigit() or c == '.')
                    conf = float(conf_text)
                    # If it's a percentage, convert to decimal
                    if conf > 1:
                        conf /= 100
                    confidence = conf
                except Exception as e:
                    logger.warning(f"Error parsing confidence: {str(e)}")
            
            elif "Reasoning:" in line:
                # Get the rest of the line after "Reasoning:"
                reasoning = line.split(':', 1)[1].strip()
            
            elif "Recommendation:" in line:
                # Get the recommendation
                rec = line.split(':', 1)[1].strip().lower()
                if "approve" in rec:
                    recommendation = "Approve"
                elif "deny" in rec:
                    recommendation = "Deny"
                else:                    
                    recommendation = "Review"
        
        # Create and return the detailed analysis
        return DetailedFraudAnalysis(
            fraud_probability=fraud_probability,
            confidence=confidence,
            reasoning=reasoning,
            recommendation=recommendation,
            full_analysis=response,
            retrieved_patterns=[]  # Will be filled later
        )
    
    def _initialize_mock_llm(self):
        """Initialize a mock LLM for testing or when API is unavailable."""
        # First, check for online Ollama if enabled
        try:
            # Check if online Ollama is configured and enabled
            if hasattr(settings, 'USE_ONLINE_OLLAMA') and settings.USE_ONLINE_OLLAMA:
                try:
                    # Initialize the LocalLLMService which supports both online and local Ollama
                    local_llm_service = LocalLLMService(model_name=settings.LOCAL_LLM_MODEL, prefer_online=True)
                    
                    # Check if either online or local Ollama is available
                    if local_llm_service.available:
                        logger.info("Using Ollama service (online preferred)")
                        self.llm_service_type = "local"  # Use "local" service type for all Ollama interactions
                        self.local_llm_service = local_llm_service
                        
                        # Create a placeholder llm instance
                        from langchain_community.llms.fake import FakeListLLM
                        self.llm = FakeListLLM(responses=["Ollama service will be used"])
                        return
                except Exception as e:
                    logger.error(f"Error initializing online Ollama: {str(e)}")
            
            # If online Ollama is not configured or failed, try local LLM
            if hasattr(settings, 'USE_LOCAL_LLM') and settings.USE_LOCAL_LLM:
                try:
                    # Initialize with preference for local (fallback behavior)
                    local_llm_service = LocalLLMService(model_name=settings.LOCAL_LLM_MODEL, prefer_online=False)
                    
                    # Check if local Ollama is available
                    if local_llm_service.available:
                        logger.info(f"Using local LLM model: {settings.LOCAL_LLM_MODEL}")
                        self.llm_service_type = "local"
                        self.local_llm_service = local_llm_service
                        
                        # Create a placeholder llm instance
                        from langchain_community.llms.fake import FakeListLLM
                        self.llm = FakeListLLM(responses=["Local LLM will be used instead"])
                        return
                except Exception as e:
                    logger.error(f"Error initializing LLM services: {str(e)}")
                    logger.warning("Falling back to enhanced mock LLM")
        except Exception as e:
            logger.warning(f"Error checking local LLM settings: {str(e)}")
        
        # Use the enhanced mock LLM implementation
        try:
            logger.info("Initializing enhanced mock LLM")
            self.enhanced_mock = EnhancedMockLLM()
            self.llm_service_type = "enhanced_mock"
            
            # We need this for compatibility with the langchain pipeline
            self.llm = EnhancedFakeListLLM()
            logger.info("Initialized enhanced mock LLM for improved demonstration purposes")
        except Exception as mock_error:
            logger.error(f"Error initializing enhanced mock LLM: {str(mock_error)}")
            
            # Fall back to the basic FakeListLLM if everything else fails
            from langchain_community.llms.fake import FakeListLLM
            responses = [
                "This transaction appears legitimate based on the provided patterns and history. The transaction amount is within normal ranges for this customer, and the location is consistent with previous spending patterns. Fraud Probability: 0.15, Confidence: 0.85, Reasoning: No suspicious indicators present. Recommendation: Approve",
                "This transaction shows multiple fraud indicators and is likely fraudulent. The transaction occurred in an unusual location, with an amount significantly higher than the customer's normal spending pattern, and matches several known fraud patterns in our database. Fraud Probability: 0.85, Confidence: 0.92, Reasoning: Multiple high-risk indicators present. Recommendation: Deny",
                "This transaction requires manual review. While some aspects match legitimate spending patterns, there are some unusual characteristics that warrant further investigation. Fraud Probability: 0.55, Confidence: 0.65, Reasoning: Mixed indicators present. Recommendation: Review"
            ]
            self.llm = FakeListLLM(responses=responses)
            self.llm_service_type = "basic_mock"
            logger.info("Initialized basic mock LLM as last resort")