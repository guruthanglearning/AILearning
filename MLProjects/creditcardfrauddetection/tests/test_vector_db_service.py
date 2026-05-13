"""
Tests for app/services/vector_db_service.py (currently 37% coverage).
HuggingFaceEmbeddings and Chroma are mocked to avoid real I/O.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock
from langchain_core.documents import Document


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_chroma_mock(doc_ids=None, metadatas=None, documents=None):
    """Build a mock Chroma vector store with configurable collection results."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = len(doc_ids or [])
    mock_collection.get.return_value = {
        "ids": doc_ids or [],
        "metadatas": metadatas or [],
        "documents": documents or [],
    }

    mock_store = MagicMock()
    mock_store._collection = mock_collection
    mock_store.add_documents.return_value = None
    mock_store.as_retriever.return_value = MagicMock(
        get_relevant_documents=MagicMock(return_value=[])
    )
    return mock_store


def _make_service(chroma_mock=None):
    """Instantiate VectorDBService with all heavy deps mocked."""
    if chroma_mock is None:
        chroma_mock = _make_chroma_mock()

    mock_embedding = MagicMock()

    with patch("app.services.vector_db_service.HuggingFaceEmbeddings", return_value=mock_embedding), \
         patch("app.services.vector_db_service.Chroma", return_value=chroma_mock), \
         patch("app.services.vector_db_service.USING_CHROMA", True), \
         patch("app.services.vector_db_service.USING_PINECONE", False):
        from app.services.vector_db_service import VectorDBService
        service = VectorDBService(embedding_model=mock_embedding)
        service.vector_store = chroma_mock

    return service, chroma_mock, mock_embedding


# ── _create_fraud_pattern_text ────────────────────────────────────────────────

class TestCreateFraudPatternText:
    def setup_method(self):
        self.service, _, _ = _make_service()

    def test_includes_case_id(self):
        result = self.service._create_fraud_pattern_text({"case_id": "FRD-001"})
        assert "FRD-001" in result

    def test_includes_fraud_type(self):
        result = self.service._create_fraud_pattern_text({"fraud_type": "Card Testing"})
        assert "Card Testing" in result

    def test_includes_amount(self):
        result = self.service._create_fraud_pattern_text({"amount": 999.99})
        assert "999.99" in result

    def test_includes_pattern_description(self):
        result = self.service._create_fraud_pattern_text({
            "pattern_description": "Rapid small transactions"
        })
        assert "Rapid small transactions" in result

    def test_includes_indicators(self):
        result = self.service._create_fraud_pattern_text({
            "indicators": ["unusual location", "high value"]
        })
        assert "unusual location" in result
        assert "high value" in result

    def test_missing_fields_use_defaults(self):
        result = self.service._create_fraud_pattern_text({})
        assert "unknown" in result


# ── add_fraud_patterns ────────────────────────────────────────────────────────

class TestAddFraudPatterns:
    def setup_method(self):
        self.service, self.chroma_mock, _ = _make_service()

    def test_returns_positive_count(self):
        patterns = [{"case_id": "FRD-001", "fraud_type": "Card Testing", "amount": 9.99}]
        result = self.service.add_fraud_patterns(patterns)
        assert result > 0

    def test_add_documents_called(self):
        patterns = [{"case_id": "FRD-001"}]
        self.service.add_fraud_patterns(patterns)
        assert self.chroma_mock.add_documents.called

    def test_multiple_patterns(self):
        patterns = [
            {"case_id": "FRD-001", "fraud_type": "Type A"},
            {"case_id": "FRD-002", "fraud_type": "Type B"},
        ]
        result = self.service.add_fraud_patterns(patterns)
        assert result >= 2

    def test_optional_metadata_fields_preserved(self):
        patterns = [{
            "case_id": "FRD-001",
            "_original_name": "My Pattern",
            "_original_description": "My desc",
            "_similarity_threshold": 0.75,
        }]
        # Should not raise
        self.service.add_fraud_patterns(patterns)

    def test_indicators_joined_as_string(self):
        """indicators list should be joined as a comma-separated string in metadata."""
        captured_docs = []
        self.chroma_mock.add_documents.side_effect = lambda docs: captured_docs.extend(docs)

        patterns = [{"case_id": "FRD-001", "indicators": ["ind1", "ind2"]}]
        self.service.add_fraud_patterns(patterns)

        assert any("ind1,ind2" in str(d.metadata.get("indicators", "")) for d in captured_docs)

    def test_empty_list_returns_zero(self):
        result = self.service.add_fraud_patterns([])
        assert result == 0


# ── add_feedback_as_pattern ───────────────────────────────────────────────────

class TestAddFeedbackAsPattern:
    def setup_method(self):
        self.service, self.chroma_mock, _ = _make_service()

    def test_returns_count(self):
        result = self.service.add_feedback_as_pattern("tx_001", "This was fraud", True)
        assert result > 0

    def test_false_positive_label(self):
        captured_docs = []
        self.chroma_mock.add_documents.side_effect = lambda docs: captured_docs.extend(docs)
        self.service.add_feedback_as_pattern("tx_001", "Legitimate transaction", False)
        assert any("False Positive" in str(d.metadata) for d in captured_docs)

    def test_verified_fraud_label(self):
        captured_docs = []
        self.chroma_mock.add_documents.side_effect = lambda docs: captured_docs.extend(docs)
        self.service.add_feedback_as_pattern("tx_002", "Confirmed fraud", True)
        assert any("Verified Fraud" in str(d.metadata) for d in captured_docs)


# ── search_similar_patterns ───────────────────────────────────────────────────

class TestSearchSimilarPatterns:
    def setup_method(self):
        self.service, self.chroma_mock, _ = _make_service()

    def test_returns_list(self):
        result = self.service.search_similar_patterns("fraud transaction")
        assert isinstance(result, list)

    def test_returns_docs_from_retriever(self):
        mock_doc = Document(page_content="fraud pattern", metadata={"case_id": "FRD-001"})
        self.chroma_mock.as_retriever.return_value.get_relevant_documents.return_value = [mock_doc]
        result = self.service.search_similar_patterns("fraud transaction")
        assert len(result) == 1
        assert result[0].metadata["case_id"] == "FRD-001"

    def test_exception_returns_empty_list(self):
        self.chroma_mock.as_retriever.side_effect = RuntimeError("retriever error")
        result = self.service.search_similar_patterns("test")
        assert result == []

    def test_custom_k(self):
        self.service.search_similar_patterns("test", k=10)
        call = self.chroma_mock.as_retriever.call_args
        assert call[1]["search_kwargs"]["k"] == 10


# ── get_stats ─────────────────────────────────────────────────────────────────

class TestGetStats:
    def setup_method(self):
        self.service, self.chroma_mock, _ = _make_service()

    def test_returns_dict(self):
        self.chroma_mock._collection.count.return_value = 42
        result = self.service.get_stats()
        assert isinstance(result, dict)

    def test_contains_vector_store_type(self):
        result = self.service.get_stats()
        assert "vector_store_type" in result

    def test_contains_embedding_model(self):
        result = self.service.get_stats()
        assert "embedding_model" in result

    def test_total_vectors_from_chroma(self):
        self.chroma_mock._collection.count.return_value = 99
        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = self.service.get_stats()
        assert "total_vectors" in result


# ── get_all_fraud_patterns ────────────────────────────────────────────────────

class TestGetAllFraudPatterns:
    def test_returns_patterns_from_chroma(self):
        chroma_mock = _make_chroma_mock(
            doc_ids=["id1", "id2"],
            metadatas=[
                {"case_id": "FRD-001", "fraud_type": "Card Testing", "amount": 9.99,
                 "merchant_category": "Digital", "detection_date": "2025-01-01",
                 "method": "API", "currency": "USD"},
                {"case_id": "FRD-002", "fraud_type": "Account Takeover", "amount": 500.0,
                 "merchant_category": "Luxury", "detection_date": "2025-01-02",
                 "method": "Social", "currency": "USD"},
            ],
            documents=["doc content 1", "doc content 2"],
        )
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.get_all_fraud_patterns()

        assert len(result) == 2
        ids = [p["id"] for p in result]
        assert "FRD-001" in ids

    def test_uses_original_name_when_present(self):
        chroma_mock = _make_chroma_mock(
            doc_ids=["id1"],
            metadatas=[{"case_id": "FRD-001", "_original_name": "My Custom Pattern",
                        "fraud_type": "Card Testing", "amount": 9.99,
                        "merchant_category": "Digital", "detection_date": "2025-01-01",
                        "method": "API", "currency": "USD"}],
            documents=["content"],
        )
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.get_all_fraud_patterns()

        assert result[0]["name"] == "My Custom Pattern"

    def test_indicators_parsed_from_string(self):
        chroma_mock = _make_chroma_mock(
            doc_ids=["id1"],
            metadatas=[{"case_id": "FRD-001", "fraud_type": "Type A",
                        "indicators": "ind1,ind2,ind3", "amount": 0.0,
                        "merchant_category": "", "detection_date": "",
                        "method": "", "currency": "USD"}],
            documents=["content"],
        )
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.get_all_fraud_patterns()

        assert result[0]["pattern"]["indicators"] == ["ind1", "ind2", "ind3"]

    def test_empty_collection_seeds_defaults(self):
        """When no patterns exist, defaults are seeded and re-fetched."""
        call_count = {"count": 0}
        empty_result = {"ids": [], "metadatas": [], "documents": []}
        seeded_result = {
            "ids": ["id1"],
            "metadatas": [{"case_id": "default_001", "fraud_type": "Card Not Present",
                           "amount": 899.99, "merchant_category": "Electronics",
                           "detection_date": "2025-01-01", "method": "Online",
                           "currency": "USD"}],
            "documents": ["content"],
        }

        def get_side_effect(**kwargs):
            call_count["count"] += 1
            return empty_result if call_count["count"] == 1 else seeded_result

        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.side_effect = get_side_effect
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.get_all_fraud_patterns()

        assert len(result) >= 1

    def test_exception_returns_empty_list(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.side_effect = RuntimeError("DB error")
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.get_all_fraud_patterns()

        assert result == []


# ── delete_fraud_pattern ──────────────────────────────────────────────────────

class TestDeleteFraudPattern:
    def test_deletes_existing_pattern(self):
        chroma_mock = _make_chroma_mock(doc_ids=["id1"], metadatas=[{}], documents=[""])
        chroma_mock._collection.get.return_value = {"ids": ["id1"]}
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.delete_fraud_pattern("FRD-001")

        assert result is True
        chroma_mock._collection.delete.assert_called_once()

    def test_returns_false_for_missing_pattern(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.return_value = {"ids": []}
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.delete_fraud_pattern("NONEXISTENT")

        assert result is False

    def test_exception_returns_false(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.side_effect = RuntimeError("DB error")
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.delete_fraud_pattern("FRD-001")

        assert result is False


# ── pattern_exists ────────────────────────────────────────────────────────────

class TestPatternExists:
    def test_returns_true_when_found(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.return_value = {"ids": ["id1"]}
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.pattern_exists("FRD-001")

        assert result is True

    def test_returns_false_when_not_found(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.return_value = {"ids": []}
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.pattern_exists("GHOST")

        assert result is False

    def test_exception_returns_false(self):
        chroma_mock = _make_chroma_mock()
        chroma_mock._collection.get.side_effect = RuntimeError("error")
        service, _, _ = _make_service(chroma_mock)

        with patch("app.services.vector_db_service.USING_CHROMA", True), \
             patch("app.services.vector_db_service.USING_PINECONE", False):
            result = service.pattern_exists("FRD-001")

        assert result is False
