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
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema import Document
import torch

from app.api.models import Transaction, DetailedFraudAnalysis
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLMs for fraud detection."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.llm = None
        self.embedding_model = None
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize the LLM and embedding models."""
        try:
            logger.info("Initializing LLM and embedding models...")
            
            # Initialize the embedding model
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
            )
            logger.info(f"Initialized embedding model: {settings.EMBEDDING_MODEL}")
            
            # Initialize the LLM
            self.llm = ChatOpenAI(
                model_name=settings.LLM_MODEL,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info(f"Initialized LLM: {settings.LLM_MODEL}")
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            raise
    
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
        logger.info(f"Analyzing transaction with LLM")
        
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
            logger.error(f"Error during LLM analysis: {str(e)}")
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