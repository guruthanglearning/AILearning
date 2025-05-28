'''
Vector database service for storing and retrieving fraud patterns.
This module handles interaction with the vector database using embeddings.
'''

import logging
import os
from typing import Dict, List, Any, Optional
import time
import json

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
    from pinecone_client import Pinecone
    from langchain_community.vectorstores import Pinecone as LangchainPinecone
    USING_PINECONE = True
except ImportError:
    USING_PINECONE = False

from app.core.config import settings
from app.models.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

class VectorDBService:
    '''Service for interacting with the vector database.'''
    
    def __init__(self, embedding_model=None):
        '''
        Initialize the vector database service.
        
        Args:
            embedding_model: Optional pre-initialized embedding model
        '''
        self.vector_store = None
        self.embedding_model = embedding_model
        self.using_pinecone = False
        self.using_chroma = False
        self.initialize_vector_store()
    
    def initialize_vector_store(self):
        '''Initialize the vector database.'''
        try:
            logger.info('Initializing vector store...')
            
            # Initialize embedding model if not provided
            if self.embedding_model is None:
                logger.info(f'Initializing embedding model: {settings.EMBEDDING_MODEL}')
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL,
                    model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
                )
                logger.info(f'Embedding model initialized on {"GPU" if torch.cuda.is_available() else "CPU"}')
            
            # Initialize vector store based on what's available
            if USING_PINECONE and settings.PINECONE_API_KEY and settings.USE_PINECONE:
                self._initialize_pinecone()
            elif USING_CHROMA:
                self._initialize_chroma()
            else:
                logger.warning('No supported vector database available. Using in-memory vector store.')
                self._initialize_in_memory()
            
            # Check if we have any patterns, if not seed with default ones
            self._seed_default_patterns_if_empty()
            
            logger.info('Vector store initialization complete')
            
        except Exception as e:
            logger.error(f'Error initializing vector store: {str(e)}')
            raise
    
    def _initialize_pinecone(self):
        '''Initialize Pinecone vector store.'''
        logger.info('Initializing Pinecone vector store...')
        
        # Initialize Pinecone
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Create index if it doesn't exist
        existing_indexes = [idx['name'] for idx in pc.list_indexes()]
        if settings.VECTOR_INDEX_NAME not in existing_indexes:
            logger.info(f'Creating new Pinecone index: {settings.VECTOR_INDEX_NAME}')
            pc.create_index(
                name=settings.VECTOR_INDEX_NAME,
                dimension=settings.VECTOR_DIMENSION,
                metric='cosine'
            )
        else:
            logger.info(f'Using existing Pinecone index: {settings.VECTOR_INDEX_NAME}')
        
        # Connect to index
        index = pc.Index(settings.VECTOR_INDEX_NAME)
        
        # Initialize langchain vector store
        self.vector_store = LangchainPinecone(index, self.embedding_model, 'text')
        self.using_pinecone = True
        self.using_chroma = False
        logger.info('Pinecone vector store initialized successfully')
    
    def _initialize_chroma(self):
        '''Initialize Chroma vector store.'''
        logger.info('Initializing Chroma vector store...')
        
        # Define persistence directory
        persist_directory = os.path.join(os.getcwd(), 'data', 'chroma_db')
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model
        )
        self.using_chroma = True
        self.using_pinecone = False
        logger.info(f'Chroma vector store initialized at {persist_directory}')
    
    def _initialize_in_memory(self):
        '''Initialize an in-memory vector store for development/testing.'''
        logger.info('Initializing in-memory vector store...')
        
        # Use Chroma with no persistence directory for in-memory storage
        self.vector_store = Chroma(
            embedding_function=self.embedding_model
        )
        self.using_chroma = True
        self.using_pinecone = False
        logger.info('In-memory vector store initialized successfully')
    
    def add_fraud_patterns(self, fraud_data: List[Dict[str, Any]]) -> int:
        '''
        Add fraud patterns to the vector store.
        
        Args:
            fraud_data: List of fraud pattern data
            
        Returns:
            Number of patterns added
        '''
        start_time = time.time()
        logger.info(f'Adding {len(fraud_data)} fraud patterns to vector store')
        
        try:
            # Import the filter_complex_metadata utility
            from langchain_community.vectorstores.utils import filter_complex_metadata
        except ImportError:
            logger.warning("Could not import filter_complex_metadata. Will stringify complex metadata values.")
            filter_complex_metadata = None
        
        documents = []
        for fraud_case in fraud_data:
            # Create detailed text description of the fraud case
            fraud_text = self._create_fraud_pattern_text(fraud_case)
            
            # Store pattern as JSON string instead of a dict to avoid the complex metadata issue
            pattern_str = json.dumps(fraud_case.get('pattern', {})) if fraud_case.get('pattern') else "{}"
            
            # Create metadata with only simple types
            metadata = {
                'case_id': fraud_case.get('id', fraud_case.get('case_id', 'unknown')),
                'name': fraud_case.get('name', 'Unnamed Pattern'),
                'description': fraud_case.get('description', ''),
                'pattern_json': pattern_str,  # Store as JSON string
                'similarity_threshold': float(fraud_case.get('similarity_threshold', 0.8)),
                'created_at': str(fraud_case.get('created_at', '')),
                'fraud_type': str(fraud_case.get('fraud_type', 'unknown')),
                'amount': float(fraud_case.get('amount', 0.0)),
                'detection_date': str(fraud_case.get('detection_date', '')),
                'merchant_category': str(fraud_case.get('merchant_category', '')),
                'source': 'historical_fraud_database'
            }
            
            # Create document with metadata
            doc = Document(
                page_content=fraud_text,
                metadata=metadata
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
        
        logger.info(f'Successfully added {len(split_docs)} document chunks to vector store '
                    f'in {time.time() - start_time:.2f} seconds')
                    
        return len(split_docs)
    
    def _create_fraud_pattern_text(self, fraud_case: Dict[str, Any]) -> str:
        '''
        Create a text description of a fraud pattern.
        
        Args:
            fraud_case: Fraud pattern data
            
        Returns:
            Text description of the fraud pattern
        '''
        # Basic fraud case information
        fraud_text = f'''
        Fraud Case ID: {fraud_case.get('case_id', 'unknown')}
        Detection Date: {fraud_case.get('detection_date', '')}
        Fraud Type: {fraud_case.get('fraud_type', 'unknown')}
        Fraud Method: {fraud_case.get('method', 'unknown')}
        Amount: {fraud_case.get('amount', 0.0)} {fraud_case.get('currency', 'USD')}
        Merchant Category: {fraud_case.get('merchant_category', 'unknown')}
        '''
        
        # Add pattern description if available
        if 'pattern_description' in fraud_case:
            fraud_text += f'\nPattern Description:\n{fraud_case["pattern_description"]}\n'
        
        # Add indicators if available
        if 'indicators' in fraud_case and isinstance(fraud_case['indicators'], list):
            fraud_text += '\nIndicators:\n'
            for indicator in fraud_case['indicators']:
                fraud_text += f'- {indicator}\n'
        
        return fraud_text
    
    def add_feedback_as_pattern(self, transaction_id: str, feedback: str, is_fraud: bool) -> int:
        '''
        Add analyst feedback as a new fraud pattern.
        
        Args:
            transaction_id: ID of the transaction
            feedback: Analyst feedback text
            is_fraud: Whether the transaction was actually fraudulent
            
        Returns:
            Number of patterns added
        '''
        logger.info(f'Adding feedback for transaction {transaction_id} as new pattern')
        
        # Create a new fraud pattern document from the feedback
        fraud_case = {
            'case_id': f'feedback_{transaction_id}',
            'detection_date': time.strftime('%Y-%m-%d'),
            'fraud_type': 'Verified Fraud' if is_fraud else 'False Positive',
            'method': 'Analyst Feedback',
            'pattern_description': feedback
        }
        
        # Add to vector store
        return self.add_fraud_patterns([fraud_case])
    
    def search_similar_patterns(self, transaction_text: str, k: int = 5) -> List[Document]:
        '''
        Search for similar fraud patterns to a transaction.
        
        Args:
            transaction_text: Text description of the transaction
            k: Number of similar patterns to retrieve
            
        Returns:
            List of similar fraud pattern documents
        '''
        start_time = time.time()
        logger.info(f'Searching for similar patterns to transaction')
        
        try:
            # Create a retriever with the vector store
            retriever = self.vector_store.as_retriever(
                search_type='similarity',
                search_kwargs={'k': k}
            )
            
            # Get the similar documents
            similar_docs = retriever.get_relevant_documents(transaction_text)
            
            logger.info(f'Found {len(similar_docs)} similar patterns '
                       f'in {time.time() - start_time:.2f} seconds')
            
            return similar_docs
            
        except Exception as e:
            logger.error(f'Error searching for similar patterns: {str(e)}')
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        '''
        Get statistics about the vector store.
        
        Returns:
            Dictionary of vector store statistics
        '''
        stats = {
            'vector_store_type': type(self.vector_store).__name__,
            'embedding_model': settings.EMBEDDING_MODEL,
            'vector_dimension': settings.VECTOR_DIMENSION
        }
        
        # Try to get collection stats if available
        try:
            if USING_PINECONE and isinstance(self.vector_store, LangchainPinecone):
                # For Pinecone, try to get stats
                try:
                    index_stats = self.vector_store._index.describe_index_stats()
                    stats['total_vectors'] = index_stats.get('total_vector_count', 0)
                except:
                    stats['total_vectors'] = 'unknown'
            
            elif USING_CHROMA and hasattr(self.vector_store, '_collection'):
                # For Chroma, get collection stats
                stats['total_vectors'] = self.vector_store._collection.count()
            
            else:
                stats['total_vectors'] = 'unknown'
        
        except Exception as e:
            logger.warning(f'Error getting vector store stats: {str(e)}')
            stats['total_vectors'] = 'unknown'
        
        return stats
    
    def get_all_fraud_patterns(self) -> List[Dict[str, Any]]:
        '''
        Get all fraud patterns from the vector store.
        
        Returns:
            List of fraud patterns with their metadata
        '''
        logger.info('Retrieving all fraud patterns from vector store')
        
        try:
            # Get all documents from the vector store
            if hasattr(self, 'using_pinecone') and self.using_pinecone:
                # For Pinecone, we need to make a special query to retrieve all vectors
                # Get the first 100 patterns (can be paginated in a real implementation)
                results = self.vector_store.similarity_search("fraud pattern", k=100)
            else:
                # For in-memory stores like Chroma, we can retrieve all documents
                # The query is a dummy to retrieve everything (sorted by relevance)
                results = self.vector_store.similarity_search("fraud pattern", k=100)
            
            # Convert to a list of dictionaries with pattern info
            patterns = []
            for doc in results:
                metadata = doc.metadata
                pattern_id = metadata.get('case_id', 'unknown')
                
                # Parse the pattern JSON string back to a dict
                pattern_dict = {}
                pattern_json = metadata.get('pattern_json', '{}')
                try:
                    pattern_dict = json.loads(pattern_json)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Could not parse pattern JSON for pattern {pattern_id}")
                
                pattern = {
                    "id": pattern_id,
                    "name": metadata.get('name', f'Pattern {pattern_id}'),
                    "description": metadata.get('description', ''),
                    "pattern": pattern_dict,
                    "similarity_threshold": float(metadata.get('similarity_threshold', 0.8)),
                    "created_at": metadata.get('created_at', '')
                }
                patterns.append(pattern)
            
            logger.info(f"Retrieved {len(patterns)} fraud patterns")
            return patterns
            
        except Exception as e:
            logger.error(f"Error retrieving fraud patterns: {str(e)}", exc_info=True)
            # Return an empty list if retrieval failed
            return []
    
    def _seed_default_patterns_if_empty(self):
        '''Seed the vector store with default patterns if it's empty.'''
        # Check if there are any patterns
        patterns = self.get_all_fraud_patterns()
        if not patterns:
            logger.info('No patterns found in vector store. Seeding with default patterns...')
            default_patterns = [
                {
                    "id": "pattern_001",
                    "name": "High-value Electronics Purchase",
                    "description": "Unusually high-value purchase from electronics retailer, especially from new device or unusual location.",
                    "pattern": {
                        "merchant_category": "Electronics",
                        "transaction_type": "online",
                        "indicators": ["high_amount", "new_device", "unusual_location"]
                    },
                    "similarity_threshold": 0.85,
                    "created_at": "2025-05-01T10:00:00Z"
                },
                {
                    "id": "pattern_002",
                    "name": "Multiple Small Transactions",
                    "description": "Series of small transactions in rapid succession, testing card validity.",
                    "pattern": {
                        "transaction_frequency": "high",
                        "amount_range": "low",
                        "time_window": "short"
                    },
                    "similarity_threshold": 0.80,
                    "created_at": "2025-05-05T14:30:00Z"
                },
                {
                    "id": "pattern_003",
                    "name": "Foreign ATM Withdrawal",
                    "description": "Cash withdrawal from ATM in a country where customer has no travel history.",
                    "pattern": {
                        "transaction_type": "atm_withdrawal",
                        "location": "foreign",
                        "customer_travel_history": "none"
                    },
                    "similarity_threshold": 0.90,
                    "created_at": "2025-05-10T09:15:00Z"
                }
            ]
            # Add the default patterns
            self.add_fraud_patterns(default_patterns)
            logger.info(f'Added {len(default_patterns)} default fraud patterns to vector store')
