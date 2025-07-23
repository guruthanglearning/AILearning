"""
Enhanced Mock LLM for advanced fraud detection.
This module provides more sophisticated mock LLM capabilities for when OpenAI API is unavailable.
"""

import logging
import re
import random
from typing import Dict, List, Any, Union
import json
import time

from langchain_community.llms.fake import FakeListLLM
from langchain.schema import Document

from app.api.models import DetailedFraudAnalysis

logger = logging.getLogger(__name__)

class EnhancedMockLLM:
    """Enhanced mock LLM for fraud detection that provides more meaningful responses."""
    
    def __init__(self):
        """Initialize the enhanced mock LLM."""
        self._init_response_templates()
    
    def _init_response_templates(self):
        """Initialize response templates for different fraud scenarios."""
        self.templates = {
            # Template for legitimate transactions
            "legitimate": [
                """
                Based on the transaction details and historical fraud patterns, this transaction appears legitimate.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: The transaction amount is consistent with the customer's typical spending pattern. The merchant category and location match the customer's history. There are no suspicious patterns or indicators that match known fraud behaviors. The time and day of the transaction are also within normal parameters.
                Recommendation: Approve
                """,
                """
                This transaction shows characteristics of a legitimate purchase.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: The transaction is consistent with previous legitimate transactions from this customer. It doesn't match any of the known fraud patterns in our database, and all verification details are consistent with the customer's profile. The merchant has a good reputation with low dispute rates.
                Recommendation: Approve
                """
            ],
            
            # Template for suspicious transactions
            "suspicious": [
                """
                This transaction has some unusual characteristics that warrant further review.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: While the transaction doesn't fully match known fraud patterns, there are several concerning elements: the transaction amount is higher than the customer's usual spending, the merchant category is one the customer rarely uses, and the timing of the transaction is outside the customer's normal activity hours. These elements together suggest potential unauthorized use.
                Recommendation: Review
                """,
                """
                This transaction requires additional verification before approval.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: The transaction has mixed indicators. On one hand, it's from a merchant category the customer has used before. On the other hand, the transaction location is different from their usual pattern, and the amount is significantly higher than their average purchase in this category. There are some similarities to known card testing patterns in our database.
                Recommendation: Review
                """
            ],
            
            # Template for fraudulent transactions
            "fraudulent": [
                """
                This transaction has multiple strong fraud indicators and should be denied.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: The transaction closely matches several known fraud patterns. It involves a high-value purchase from a location significantly different from the customer's history, the merchant has been associated with previous fraud cases, and the timing and sequence of this transaction matches typical fraudulent behavior. There are clear indicators of card testing before this larger transaction.
                Recommendation: Deny
                """,
                """
                This transaction is likely fraudulent based on multiple risk factors.
                
                Fraud Probability: {probability}
                Confidence: {confidence}
                Reasoning: This transaction exhibits classic fraud indicators: it was made from an unusual location for this customer, involves a high-value electronics purchase, and occurred during unusual hours. It closely matches pattern ID {pattern_id} in our fraud database. The velocity of transactions on this account in the past 24 hours is also concerning.
                Recommendation: Deny
                """
            ]
        }
    
    def _get_response_type(self, transaction_text: str) -> str:
        """
        Determine which type of response to provide based on transaction characteristics.
        Uses keyword matching to simulate intelligent understanding.
        
        Args:
            transaction_text: The text description of the transaction
            
        Returns:
            Response type: "legitimate", "suspicious", or "fraudulent"
        """
        # Keywords that would indicate potential fraud
        fraud_keywords = [
            'unusual location', 'different country', 'multiple transactions',
            'high value', 'suspicious', 'odd hours', 'rapid succession',
            'electronics purchase', '$1000', '$2000', '$5000'
        ]
        
        # Count how many fraud indicators are present
        indicator_count = sum(1 for keyword in fraud_keywords if keyword.lower() in transaction_text.lower())
        
        if indicator_count >= 3:
            return "fraudulent"
        elif indicator_count >= 1:
            return "suspicious"
        else:
            return "legitimate"
    
    def _extract_pattern_id(self, similar_patterns: List[Document]) -> str:
        """Extract a pattern ID from the similar patterns for reference in the response."""
        if not similar_patterns:
            return "FRD-UNKNOWN"
            
        for doc in similar_patterns:
            case_id = doc.metadata.get('case_id', '')
            if case_id:
                return case_id
                
        return "FRD-UNKNOWN"
    
    def analyze_transaction(
        self,
        transaction_text: str,
        similar_patterns: List[Document]
    ) -> DetailedFraudAnalysis:
        """
        Analyze a transaction with the enhanced mock LLM.
        
        Args:
            transaction_text: Text description of the transaction
            similar_patterns: Similar fraud patterns retrieved from the vector database
            
        Returns:
            DetailedFraudAnalysis object with the analysis results
        """
        start_time = time.time()
        logger.info("Analyzing transaction with enhanced mock LLM")
        
        # Determine response type based on transaction text
        response_type = self._get_response_type(transaction_text)
        
        # Set probability and confidence based on response type
        if response_type == "legitimate":
            probability = round(random.uniform(0.05, 0.25), 2)
            confidence = round(random.uniform(0.75, 0.95), 2)
        elif response_type == "suspicious":
            probability = round(random.uniform(0.35, 0.65), 2)
            confidence = round(random.uniform(0.60, 0.80), 2)
        else:  # fraudulent
            probability = round(random.uniform(0.75, 0.95), 2)
            confidence = round(random.uniform(0.80, 0.98), 2)
        
        # Select a template and format it
        template = random.choice(self.templates[response_type])
        pattern_id = self._extract_pattern_id(similar_patterns)
        
        response = template.format(
            probability=probability,
            confidence=confidence,
            pattern_id=pattern_id
        )
        
        # Parse the response to extract structured data
        analysis = self._parse_response(response)
        
        # Add the full analysis text
        analysis.full_analysis = response
        
        # Add the retrieved patterns for reference
        pattern_ids = [doc.metadata.get("case_id", "unknown") for doc in similar_patterns]
        analysis.retrieved_patterns = pattern_ids
        
        logger.info(f"Enhanced mock LLM analysis completed in {time.time() - start_time:.2f} seconds")
        return analysis
    
    def _parse_response(self, response: str) -> DetailedFraudAnalysis:
        """Parse the response to extract structured information."""
        # Default values
        fraud_probability = 0.5
        confidence = 0.5
        reasoning = "Analysis inconclusive"
        recommendation = "Review"
        
        # Extract probability
        prob_match = re.search(r"Fraud Probability:\s*(\d+\.\d+)", response)
        if prob_match:
            fraud_probability = float(prob_match.group(1))
            
        # Extract confidence
        conf_match = re.search(r"Confidence:\s*(\d+\.\d+)", response)
        if conf_match:
            confidence = float(conf_match.group(1))
            
        # Extract reasoning (everything between "Reasoning:" and "Recommendation:")
        reasoning_match = re.search(r"Reasoning:\s*(.*?)(?=\s*Recommendation:)", response, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
            
        # Extract recommendation
        if "Approve" in response:
            recommendation = "Approve"
        elif "Deny" in response:
            recommendation = "Deny"
        else:
            recommendation = "Review"
            
        return DetailedFraudAnalysis(
            fraud_probability=fraud_probability,
            confidence=confidence,
            reasoning=reasoning,
            recommendation=recommendation,
            full_analysis=response,
            retrieved_patterns=[]  # Will be filled later
        )

class EnhancedFakeListLLM(FakeListLLM):
    """Enhanced FakeListLLM that selects responses based on transaction content."""
    
    def __init__(self, responses=None):
        if responses is None:
            responses = [
                "This transaction appears legitimate based on the provided patterns and history. The transaction amount is within normal ranges for this customer, and the location is consistent with previous spending patterns. Fraud Probability: 0.15, Confidence: 0.85, Reasoning: No suspicious indicators present. Recommendation: Approve",
                "This transaction shows multiple fraud indicators and is likely fraudulent. The transaction occurred in an unusual location, with an amount significantly higher than the customer's normal spending pattern, and matches several known fraud patterns in our database. Fraud Probability: 0.92, Confidence: 0.87, Reasoning: Multiple high-risk indicators present. Recommendation: Deny",
                "This transaction requires manual review. While some aspects match legitimate spending patterns, there are some unusual characteristics that warrant further investigation. Fraud Probability: 0.55, Confidence: 0.65, Reasoning: Mixed indicators present. Recommendation: Review"
            ]
        super().__init__(responses=responses)
        
    def _select_relevant_response(self, prompt):
        """Select a response based on the content of the prompt."""
        # Check if the prompt contains any high-risk indicators
        high_risk_indicators = [
            "unusual location", "different country", "multiple transactions",
            "high value", "suspicious", "odd hours", "rapid succession"
        ]
        
        # Count matches
        prompt = prompt.lower()
        high_risk_count = sum(1 for indicator in high_risk_indicators if indicator in prompt)
        
        # Select response based on risk level
        if high_risk_count >= 2:
            # High risk - return deny response
            return self.responses[1]
        elif high_risk_count >= 1:
            # Medium risk - return review response
            return self.responses[2]
        else:
            # Low risk - return approve response
            return self.responses[0]
    
    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs) -> str:
        """Override _call to select the most relevant response."""
        return self._select_relevant_response(prompt)
