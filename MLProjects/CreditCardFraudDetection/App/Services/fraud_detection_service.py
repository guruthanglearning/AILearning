"""
Fraud detection service that coordinates ML, LLM, and vector database components.
This is the main service that handles the fraud detection pipeline.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from app.api.models import Transaction, FraudDetectionResponse, FeedbackModel, DetailedFraudAnalysis
from app.models.ml_model import MLModel
from app.services.llm_service import LLMService
from app.services.vector_db_service import VectorDBService
from app.utils.feature_engineering import (
    engineer_features,
    create_transaction_text,
    select_features_for_ml
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class FraudDetectionService:
    """Service for detecting fraud in credit card transactions."""
    
    def __init__(self):
        """Initialize the fraud detection service."""
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components of the fraud detection system."""
        try:
            logger.info("Initializing fraud detection components...")
            
            # Initialize the ML model
            self.ml_model = MLModel()
            logger.info("ML model initialized")
            
            # Initialize the vector database service
            self.vector_db_service = VectorDBService()
            logger.info("Vector DB service initialized")
            
            # Initialize the LLM service (with shared embedding model for efficiency)
            self.llm_service = LLMService()
            logger.info("LLM service initialized")
            
            logger.info("All fraud detection components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing fraud detection components: {str(e)}")
            raise
    
    def detect_fraud(self, transaction: Transaction) -> FraudDetectionResponse:
        """
        Detect fraud in a credit card transaction.
        This is the main method that coordinates the fraud detection pipeline.
        
        Args:
            transaction: The transaction to analyze
            
        Returns:
            FraudDetectionResponse with the fraud detection result
        """
        start_time = time.time()
        transaction_id = transaction.transaction_id
        logger.info(f"Processing transaction {transaction_id}")
        
        try:
            # Step 1: Feature Engineering
            features = engineer_features(transaction)
            logger.info(f"Extracted {len(features)} features for transaction {transaction_id}")
            
            # Step 2: Initial ML screening
            ml_features = select_features_for_ml(features)
            fraud_probability, ml_confidence = self.ml_model.predict(ml_features)
            logger.info(f"ML model prediction: probability={fraud_probability:.4f}, confidence={ml_confidence:.4f}")
            
            # Step 3: Create transaction text for LLM
            transaction_text = create_transaction_text(transaction, features)
            
            # Step 4: Determine if LLM analysis is needed
            # Skip LLM for very clear cases (high confidence and low amount)
            requires_llm = (
                ml_confidence < 0.95 or                # Not highly confident
                (0.2 < fraud_probability < 0.8) or     # Borderline case
                transaction.amount > 1000 or           # High value transaction
                features["merchant_risk_score"] > 0.6  # Risky merchant
            )
            
            llm_analysis = None
            if requires_llm:
                # Step 5: Retrieve similar fraud patterns
                similar_patterns = self.vector_db_service.search_similar_patterns(transaction_text)
                logger.info(f"Retrieved {len(similar_patterns)} similar patterns for transaction {transaction_id}")
                
                # Step 6: LLM-based fraud analysis
                llm_analysis = self.llm_service.analyze_transaction(transaction_text, similar_patterns)
                logger.info(f"LLM analysis completed for transaction {transaction_id}")
                
                # Step 7: Combine ML and LLM results
                # Weight the fraud probability 40% ML, 60% LLM
                fraud_probability = (0.4 * fraud_probability) + (0.6 * llm_analysis.fraud_probability)
                
                # Use the more confident source for confidence score
                confidence_score = max(ml_confidence, llm_analysis.confidence)
                
                # Use LLM reasoning
                decision_reason = llm_analysis.reasoning
            else:
                # Step 5 (alternative): Use ML model result directly
                confidence_score = ml_confidence
                decision_reason = "Determined by ML model with high confidence"
                logger.info(f"Skipped LLM analysis for transaction {transaction_id} - clear ML result")
            
            # Step 8: Make final decision
            is_fraud = fraud_probability > 0.5
            requires_review = confidence_score < settings.CONFIDENCE_THRESHOLD
            
            # Step 9: Create response
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            response = FraudDetectionResponse(
                transaction_id=transaction_id,
                is_fraud=is_fraud,
                confidence_score=confidence_score,
                decision_reason=decision_reason,
                requires_review=requires_review,
                processing_time_ms=processing_time
            )
            
            # Step 10: Log transaction for audit and improvement
            self._log_transaction(transaction, features, response, llm_analysis)
            
            logger.info(f"Completed fraud detection for transaction {transaction_id} "
                       f"in {processing_time:.2f}ms - Result: {'FRAUD' if is_fraud else 'LEGITIMATE'} "
                       f"(Confidence: {confidence_score:.4f})")
            
            return response
            
        except Exception as e:
            logger.error(f"Error detecting fraud for transaction {transaction_id}: {str(e)}")
            # Return a conservative default response in case of error
            return FraudDetectionResponse(
                transaction_id=transaction_id,
                is_fraud=False,  # Default to letting transaction through
                confidence_score=0.1,  # Very low confidence
                decision_reason=f"Error during analysis: {str(e)}",
                requires_review=True,  # Flag for manual review
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def process_feedback(self, feedback: FeedbackModel) -> bool:
        """
        Process analyst feedback to improve the system.
        
        Args:
            feedback: Feedback from a fraud analyst
            
        Returns:
            Success status
        """
        try:
            logger.info(f"Processing feedback for transaction {feedback.transaction_id}")
            
            # Add to vector store if it's a confirmed fraud case with notes
            if feedback.actual_fraud and feedback.analyst_notes:
                self.vector_db_service.add_feedback_as_pattern(
                    feedback.transaction_id, 
                    feedback.analyst_notes,
                    feedback.actual_fraud
                )
                logger.info(f"Added fraud pattern from feedback for transaction {feedback.transaction_id}")
            
            # In a production system, we would also:
            # 1. Store feedback in a database for retraining the ML model
            # 2. Update real-time fraud rules if applicable
            # 3. Flag patterns for investigation
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing feedback for transaction {feedback.transaction_id}: {str(e)}")
            return False
    
    def _log_transaction(
        self, 
        transaction: Transaction, 
        features: Dict[str, Any], 
        response: FraudDetectionResponse,
        llm_analysis: Optional[DetailedFraudAnalysis] = None
    ):
        """
        Log transaction details for audit and improvement.
        In production, this would write to a database or message queue.
        
        Args:
            transaction: Transaction data
            features: Extracted features
            response: Fraud detection response
            llm_analysis: LLM analysis results (if available)
        """
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "transaction_id": transaction.transaction_id,
            "card_id": transaction.card_id,
            "merchant_id": transaction.merchant_id,
            "amount": transaction.amount,
            "currency": transaction.currency,
            "merchant_category": transaction.merchant_category,
            "is_online": transaction.is_online,
            "detection_result": {
                "is_fraud": response.is_fraud,
                "confidence_score": response.confidence_score,
                "decision_reason": response.decision_reason,
                "requires_review": response.requires_review,
                "processing_time_ms": response.processing_time_ms
            },
            "risk_factors": {
                "merchant_risk_score": features.get("merchant_risk_score", 0),
                "behavior_anomaly_score": features.get("behavior_anomaly_score", 0),
                "location_risk_score": features.get("location_risk_score", 0) if "location_risk_score" in features else None
            }
        }
        
        # Add LLM analysis if available
        if llm_analysis:
            log_entry["llm_analysis"] = {
                "fraud_probability": llm_analysis.fraud_probability,
                "confidence": llm_analysis.confidence,
                "recommendation": llm_analysis.recommendation,
                "retrieved_patterns": llm_analysis.retrieved_patterns
            }
        
        # In production, this would write to a database or message queue
        # For now, just log to the application log
        logger.info(f"Transaction log: {json.dumps(log_entry)}")
    
    def ingest_fraud_patterns(self, fraud_data: List[Dict[str, Any]]) -> int:
        """
        Ingest historical fraud patterns into the vector store.
        
        Args:
            fraud_data: List of fraud pattern data
            
        Returns:
            Number of patterns added
        """
        try:
            logger.info(f"Ingesting {len(fraud_data)} fraud patterns")
            count = self.vector_db_service.add_fraud_patterns(fraud_data)
            logger.info(f"Successfully ingested {count} fraud patterns")
            return count
        except Exception as e:
            logger.error(f"Error ingesting fraud patterns: {str(e)}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of the fraud detection system.
        
        Returns:
            Dictionary with system status information
        """
        vector_db_stats = self.vector_db_service.get_stats()
        
        return {
            "status": "healthy",
            "ml_model": {
                "type": type(self.ml_model).__name__,
            },
            "llm": {
                "model": settings.LLM_MODEL,
            },
            "vector_db": vector_db_stats,
            "config": {
                "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
                "similarity_threshold": settings.DEFAULT_SIMILARITY_THRESHOLD,
                "transaction_history_window": settings.TRANSACTION_HISTORY_WINDOW
            }
        }