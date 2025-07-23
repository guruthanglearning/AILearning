"""
Vector database service for storing and retrieving fraud patterns.
This module handles interaction with the vector database using embeddings.
"""

import logging
import os
from typing import Dict, List, Any, Optional
import time

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import torch

# We can use either Pinecone or another vector DB like Chroma
try:
    from langchain_community.vectorstores import Chroma
    USING_CHROMA = True
except ImportError:
    USING_CHROMA = False

try:
    from pinecone import Pinecone, ServerlessSpec
    from langchain_community.vectorstores import Pinecone as LangchainPinecone
    USING_PINECONE = True
except ImportError:
    USING_PINECONE = False

from app.core.config import settings
from app.models.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

class VectorDBService:
    """Service for interacting with the vector database."""
    
    def __init__(self, embedding_model=None):
        """
        Initialize the vector database service.
        
        Args:
            embedding_model: Optional pre-initialized embedding model
        """
        self.vector_store = None
        self.embedding_model = embedding_model
        self.initialize_vector_store()
    
    def initialize_vector_store(self):
        """Initialize the vector database."""
        try:
            logger.info("Initializing vector store...")
            
            # Initialize embedding model if not provided
            if self.embedding_model is None:
                logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL}")
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
                )
                logger.info(f"Embedding model initialized on {'GPU' if torch.cuda.is_available() else 'CPU'}")
            
            # Initialize vector store based on what's available
            if USING_PINECONE and settings.PINECONE_API_KEY:
                self._initialize_pinecone()
            elif USING_CHROMA:
                self._initialize_chroma()
            else:
                logger.warning("No supported vector database available. Using in-memory vector store.")
                self._initialize_in_memory()
            
            logger.info("Vector store initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def _initialize_pinecone(self):
        """Initialize Pinecone vector store."""
        logger.info("Initializing Pinecone vector store...")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Create index if it doesn't exist
        if settings.VECTOR_INDEX_NAME not in pc.list_indexes().names():
            logger.info(f"Creating new Pinecone index: {settings.VECTOR_INDEX_NAME}")
            pc.create_index(
                name=settings.VECTOR_INDEX_NAME,
                dimension=settings.VECTOR_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )
        else:
            logger.info(f"Using existing Pinecone index: {settings.VECTOR_INDEX_NAME}")
        
        # Connect to index
        index = pc.Index(settings.VECTOR_INDEX_NAME)
        
        # Initialize langchain vector store
        self.vector_store = LangchainPinecone(index, self.embedding_model, "text")
        logger.info("Pinecone vector store initialized successfully")
    
    def _initialize_chroma(self):
        """Initialize Chroma vector store."""
        logger.info("Initializing Chroma vector store...")
        
        # Define persistence directory
        persist_directory = os.path.join(os.getcwd(), "data", "chroma_db")
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model
        )
        logger.info(f"Chroma vector store initialized at {persist_directory}")
    
    def _initialize_in_memory(self):
        """Initialize an in-memory vector store for development/testing."""
        logger.info("Initializing in-memory vector store...")
        
        # Use Chroma with no persistence directory for in-memory storage
        self.vector_store = Chroma(
            embedding_function=self.embedding_model
        )
        logger.info("In-memory vector store initialized successfully")
    
    def add_fraud_patterns(self, fraud_data: List[Dict[str, Any]]) -> int:
        """
        Add fraud patterns to the vector store.
        
        Args:
            fraud_data: List of fraud pattern data
            
        Returns:
            Number of patterns added
        """
        start_time = time.time()
        logger.info(f"Adding {len(fraud_data)} fraud patterns to vector store")
        
        documents = []
        for fraud_case in fraud_data:
            # Create detailed text description of the fraud case
            fraud_text = self._create_fraud_pattern_text(fraud_case)
            
            # Create document with metadata
            doc = Document(
                page_content=fraud_text,
                metadata={
                    "case_id": fraud_case.get("case_id", "unknown"),
                    "fraud_type": fraud_case.get("fraud_type", "unknown"),
                    "amount": fraud_case.get("amount", 0.0),
                    "detection_date": fraud_case.get("detection_date", ""),
                    "merchant_category": fraud_case.get("merchant_category", ""),
                    "source": "historical_fraud_database"
                }
            )
            documents.append(doc)
        
        # Split documents if needed (for very long descriptions)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        split_docs = text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vector_store.add_documents(split_docs)
        
        logger.info(f"Successfully added {len(split_docs)} document chunks to vector store "
                    f"in {time.time() - start_time:.2f} seconds")
                    
        return len(split_docs)
    
    def _create_fraud_pattern_text(self, fraud_case: Dict[str, Any]) -> str:
        """
        Create a text description of a fraud pattern.
        
        Args:
            fraud_case: Fraud pattern data
            
        Returns:
            Text description of the fraud pattern
        """
        # Basic fraud case information
        fraud_text = f"""
        Fraud Case ID: {fraud_case.get('case_id', 'unknown')}
        Detection Date: {fraud_case.get('detection_date', '')}
        Fraud Type: {fraud_case.get('fraud_type', 'unknown')}
        Fraud Method: {fraud_case.get('method', 'unknown')}
        Amount: {fraud_case.get('amount', 0.0)} {fraud_case.get('currency', 'USD')}
        Merchant Category: {fraud_case.get('merchant_category', 'unknown')}
        """
        
        # Add pattern description if available
        if 'pattern_description' in fraud_case:
            fraud_text += f"\nPattern Description:\n{fraud_case['pattern_description']}\n"
        
        # Add indicators if available
        if 'indicators' in fraud_case and isinstance(fraud_case['indicators'], list):
            fraud_text += "\nIndicators:\n"
            for indicator in fraud_case['indicators']:
                fraud_text += f"- {indicator}\n"
        
        return fraud_text
    
    def add_feedback_as_pattern(self, transaction_id: str, feedback: str, is_fraud: bool) -> int:
        """
        Add analyst feedback as a new fraud pattern.
        
        Args:
            transaction_id: ID of the transaction
            feedback: Analyst feedback text
            is_fraud: Whether the transaction was actually fraudulent
            
        Returns:
            Number of patterns added
        """
        logger.info(f"Adding feedback for transaction {transaction_id} as new pattern")
        
        # Create a new fraud pattern document from the feedback
        fraud_case = {
            "case_id": f"feedback_{transaction_id}",
            "detection_date": time.strftime("%Y-%m-%d"),
            "fraud_type": "Verified Fraud" if is_fraud else "False Positive",
            "method": "Analyst Feedback",
            "pattern_description": feedback
        }
        
        # Add to vector store
        return self.add_fraud_patterns([fraud_case])
    
    def search_similar_patterns(self, transaction_text: str, k: int = 5) -> List[Document]:
        """
        Search for similar fraud patterns to a transaction.
        
        Args:
            transaction_text: Text description of the transaction
            k: Number of similar patterns to retrieve
            
        Returns:
            List of similar fraud pattern documents
        """
        start_time = time.time()
        logger.info(f"Searching for similar patterns to transaction")
        
        try:
            # Create a retriever with the vector store
            retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )
            
            # Get the similar documents
            similar_docs = retriever.get_relevant_documents(transaction_text)
            
            logger.info(f"Found {len(similar_docs)} similar patterns "
                       f"in {time.time() - start_time:.2f} seconds")
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error searching for similar patterns: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary of vector store statistics
        """
        stats = {
            "vector_store_type": type(self.vector_store).__name__,
            "embedding_model": settings.EMBEDDING_MODEL,
            "vector_dimension": settings.VECTOR_DIMENSION
        }
        
        # Try to get collection stats if available
        try:
            if USING_PINECONE:
                # For Pinecone, get index stats
                index_stats = self.vector_store.index.describe_index_stats()
                stats["total_vectors"] = index_stats.get("total_vector_count", 0)
                stats["namespaces"] = list(index_stats.get("namespaces", {}).keys())
            
            elif USING_CHROMA:
                # For Chroma, get collection stats
                collection = self.vector_store._collection
                stats["total_vectors"] = collection.count()
            
            else:
                stats["total_vectors"] = "unknown"
        
        except Exception as e:
            logger.warning(f"Error getting vector store stats: {str(e)}")
            stats["total_vectors"] = "unknown"
        
        return stats

    def get_all_fraud_patterns(self) -> List[Dict[str, Any]]:
        """
        Retrieve all fraud patterns from the vector store.
        
        Returns:
            List of fraud pattern dictionaries
        """
        start_time = time.time()
        logger.info("Retrieving all fraud patterns from vector store")
        
        try:
            patterns = []
            
            if USING_PINECONE:
                # For Pinecone, we need to query to get all documents
                # This is a limitation of Pinecone - we can't easily get all documents
                # We'll do a broad similarity search with a generic query
                retriever = self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 1000}  # Get up to 1000 patterns
                )
                docs = retriever.get_relevant_documents("fraud pattern transaction")
                
                # Convert documents to pattern format
                for doc in docs:
                    pattern = {
                        "id": doc.metadata.get("case_id", "unknown"),
                        "name": doc.metadata.get("fraud_type", "Unknown Pattern"),
                        "description": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "pattern": {
                            "fraud_type": doc.metadata.get("fraud_type", "unknown"),
                            "merchant_category": doc.metadata.get("merchant_category", "unknown"),
                            "amount": doc.metadata.get("amount", 0.0),
                            "detection_date": doc.metadata.get("detection_date", "")
                        },
                        "similarity_threshold": 0.8,  # Default threshold
                        "created_at": doc.metadata.get("detection_date", "")
                    }
                    patterns.append(pattern)
                    
            elif USING_CHROMA:
                # For Chroma, we can get all documents from the collection
                collection = self.vector_store._collection
                results = collection.get()
                
                # Convert to pattern format
                for i, doc_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    content = results["documents"][i] if results["documents"] else ""
                    
                    pattern = {
                        "id": metadata.get("case_id", doc_id),
                        "name": metadata.get("fraud_type", "Unknown Pattern"),
                        "description": content[:200] + "..." if len(content) > 200 else content,
                        "pattern": {
                            "fraud_type": metadata.get("fraud_type", "unknown"),
                            "merchant_category": metadata.get("merchant_category", "unknown"),
                            "amount": metadata.get("amount", 0.0),
                            "detection_date": metadata.get("detection_date", "")
                        },
                        "similarity_threshold": 0.8,  # Default threshold
                        "created_at": metadata.get("detection_date", "")
                    }
                    patterns.append(pattern)
            
            # If no patterns found, seed with default patterns
            if not patterns:
                logger.info("No patterns found in vector store. Seeding with default patterns...")
                self._seed_default_patterns_if_empty()
                # Recursively call to get the seeded patterns
                return self.get_all_fraud_patterns()
            
            logger.info(f"Retrieved {len(patterns)} fraud patterns in {time.time() - start_time:.2f} seconds")
            return patterns
            
        except Exception as e:
            logger.error(f"Error retrieving fraud patterns: {str(e)}")
            return []

    def _seed_default_patterns_if_empty(self):
        """Seed the vector store with default patterns if it's empty."""
        try:
            # Default fraud patterns to seed the database
            default_patterns = [
                {
                    "case_id": "default_001",
                    "detection_date": "2025-01-01",
                    "fraud_type": "Card Not Present",
                    "method": "Online purchase with stolen card",
                    "amount": 899.99,
                    "currency": "USD",
                    "merchant_category": "Electronics",
                    "pattern_description": "Series of increasingly large online purchases within 24 hours, starting with small test transactions.",
                    "indicators": ["Multiple transactions increasing in value", "Purchases from unusual locations"]
                },
                {
                    "case_id": "default_002",
                    "detection_date": "2025-01-02",
                    "fraud_type": "Account Takeover",
                    "method": "Changed shipping address just before purchase",
                    "amount": 1299.95,
                    "currency": "USD",
                    "merchant_category": "Luxury Goods",
                    "pattern_description": "Account credentials changed within 48 hours of large purchase.",
                    "indicators": ["Recent account credential changes", "Shipping to forwarding service"]
                },
                {
                    "case_id": "default_003",
                    "detection_date": "2025-01-03",
                    "fraud_type": "Card Testing",
                    "method": "Rapid small transactions to test card validity",
                    "amount": 9.95,
                    "currency": "USD",
                    "merchant_category": "Digital Goods",
                    "pattern_description": "Multiple small transactions in rapid succession to test if card is valid.",
                    "indicators": ["Multiple small transactions", "Rapid succession"]
                }
            ]
            
            # Add default patterns
            self.add_fraud_patterns(default_patterns)
            
        except Exception as e:
            logger.error(f"Error seeding default patterns: {str(e)}")

    def delete_fraud_pattern(self, pattern_id: str) -> bool:
        """
        Delete a fraud pattern from the vector store.
        
        Args:
            pattern_id: ID of the pattern to delete
            
        Returns:
            True if pattern was deleted successfully, False otherwise
        """
        start_time = time.time()
        logger.info(f"Attempting to delete fraud pattern with ID: {pattern_id}")
        
        try:
            if USING_PINECONE:
                # For Pinecone, we need to delete by vector ID
                # First, find the vector(s) with this case_id in metadata
                # Note: Pinecone doesn't have a direct way to delete by metadata
                # This is a limitation of the current implementation
                logger.warning("Deleting patterns from Pinecone requires vector IDs. "
                             "Consider implementing a mapping system for production use.")
                
                # For now, we'll attempt to delete using the pattern_id as vector ID
                try:
                    self.vector_store.index.delete(ids=[pattern_id])
                    logger.info(f"Successfully deleted pattern {pattern_id} from Pinecone")
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete pattern {pattern_id} from Pinecone: {str(e)}")
                    return False
                    
            elif USING_CHROMA:
                # For Chroma, we can delete by metadata filter
                collection = self.vector_store._collection
                
                # First, check if the pattern exists
                results = collection.get(
                    where={"case_id": pattern_id}
                )
                
                if not results["ids"]:
                    logger.warning(f"Pattern with ID {pattern_id} not found in vector store")
                    return False
                
                # Delete all documents with this case_id
                collection.delete(
                    where={"case_id": pattern_id}
                )
                
                logger.info(f"Successfully deleted {len(results['ids'])} document(s) "
                          f"for pattern {pattern_id} from Chroma in {time.time() - start_time:.2f} seconds")
                return True
            
            else:
                # For in-memory vector store, try to delete by ID
                # This is a best-effort approach as the in-memory store may not support deletion
                logger.warning("Deletion from in-memory vector store may not be fully supported")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting fraud pattern {pattern_id}: {str(e)}")
            return False

    def pattern_exists(self, pattern_id: str) -> bool:
        """
        Check if a fraud pattern exists in the vector store.
        
        Args:
            pattern_id: ID of the pattern to check
            
        Returns:
            True if pattern exists, False otherwise
        """
        try:
            if USING_PINECONE:
                # For Pinecone, we'll do a fetch operation
                try:
                    result = self.vector_store.index.fetch(ids=[pattern_id])
                    return len(result.vectors) > 0
                except Exception:
                    return False
                    
            elif USING_CHROMA:
                # For Chroma, query by metadata
                collection = self.vector_store._collection
                results = collection.get(
                    where={"case_id": pattern_id}
                )
                return len(results["ids"]) > 0
            
            else:
                # For in-memory, check if we can find it in all patterns
                patterns = self.get_all_fraud_patterns()
                return any(p["id"] == pattern_id for p in patterns)
                
        except Exception as e:
            logger.error(f"Error checking if pattern {pattern_id} exists: {str(e)}")
            return False