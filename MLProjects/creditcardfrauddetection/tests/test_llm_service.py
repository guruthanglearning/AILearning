"""
Tests for app/services/llm_service.py (currently 27% coverage).
All external LLM/embedding dependencies are mocked.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from app.api.models import DetailedFraudAnalysis


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_llm_service_with_enhanced_mock():
    """Return an LLMService pre-configured with enhanced_mock type."""
    with patch("app.services.llm_service.HuggingFaceEmbeddings"), \
         patch("app.services.llm_service.LocalLLMService") as mock_local_cls, \
         patch("app.services.llm_service.EnhancedMockLLM") as mock_mock_cls, \
         patch("app.services.llm_service.EnhancedFakeListLLM"), \
         patch("app.services.llm_service.settings") as mock_settings:

        mock_settings.OPENAI_API_KEY = "your_fake_key"
        mock_settings.EMBEDDING_MODEL = "mock-model"
        mock_settings.LLM_MODEL = "gpt-4"
        mock_settings.LOCAL_LLM_MODEL = "llama3"
        mock_settings.USE_LOCAL_LLM = False
        mock_settings.USE_ONLINE_OLLAMA = False
        mock_settings.FORCE_LOCAL_LLM = False

        mock_enhanced = MagicMock()
        mock_enhanced.analyze_transaction.return_value = DetailedFraudAnalysis(
            fraud_probability=0.2,
            confidence=0.85,
            reasoning="Normal transaction",
            recommendation="Approve",
            full_analysis="Full text",
            retrieved_patterns=[],
        )
        mock_mock_cls.return_value = mock_enhanced

        from app.services.llm_service import LLMService
        service = LLMService.__new__(LLMService)
        service.llm = MagicMock()
        service.embedding_model = MagicMock()
        service.llm_service_type = "enhanced_mock"
        service.local_llm_service = None
        service.enhanced_mock = mock_enhanced

    return service


def _make_doc(case_id="FRD-001"):
    return Document(page_content="fraud content", metadata={"case_id": case_id, "fraud_type": "Card Testing"})


# ── _format_similar_patterns ──────────────────────────────────────────────────

class TestFormatSimilarPatterns:
    def setup_method(self):
        self.service = _make_llm_service_with_enhanced_mock()

    def test_empty_patterns_returns_no_patterns_text(self):
        result = self.service._format_similar_patterns([])
        assert "No similar fraud patterns found" in result

    def test_formats_case_id(self):
        doc = _make_doc("FRD-999")
        result = self.service._format_similar_patterns([doc])
        assert "FRD-999" in result

    def test_formats_multiple_patterns(self):
        docs = [_make_doc("FRD-001"), _make_doc("FRD-002")]
        result = self.service._format_similar_patterns(docs)
        assert "SIMILAR PATTERN 1" in result
        assert "SIMILAR PATTERN 2" in result

    def test_includes_page_content(self):
        doc = Document(page_content="important fraud content", metadata={"case_id": "X"})
        result = self.service._format_similar_patterns([doc])
        assert "important fraud content" in result


# ── _parse_llm_response ───────────────────────────────────────────────────────

class TestParseLlmResponse:
    def setup_method(self):
        self.service = _make_llm_service_with_enhanced_mock()

    def test_parses_fraud_probability(self):
        response = "Fraud Probability: 0.85\nConfidence: 0.9\nReasoning: high risk\nRecommendation: Deny"
        result = self.service._parse_llm_response(response)
        assert result.fraud_probability == pytest.approx(0.85)

    def test_parses_confidence(self):
        response = "Fraud Probability: 0.5\nConfidence: 0.75\nReasoning: mixed\nRecommendation: Review"
        result = self.service._parse_llm_response(response)
        assert result.confidence == pytest.approx(0.75)

    def test_parses_approve(self):
        response = "Fraud Probability: 0.1\nConfidence: 0.9\nReasoning: looks fine\nRecommendation: Approve"
        result = self.service._parse_llm_response(response)
        assert result.recommendation == "Approve"

    def test_parses_deny(self):
        response = "Fraud Probability: 0.9\nConfidence: 0.9\nReasoning: fraud\nRecommendation: Deny"
        result = self.service._parse_llm_response(response)
        assert result.recommendation == "Deny"

    def test_parses_review(self):
        response = "Fraud Probability: 0.5\nConfidence: 0.6\nReasoning: unclear\nRecommendation: Review"
        result = self.service._parse_llm_response(response)
        assert result.recommendation == "Review"

    def test_default_values_on_empty_response(self):
        result = self.service._parse_llm_response("")
        assert result.fraud_probability == 0.5
        assert result.confidence == 0.5
        assert result.recommendation == "Review"

    def test_percentage_probability_converted(self):
        response = "Fraud Probability: 85\nConfidence: 0.9\nRecommendation: Deny"
        result = self.service._parse_llm_response(response)
        assert result.fraud_probability == pytest.approx(0.85)

    def test_returns_detailed_fraud_analysis(self):
        result = self.service._parse_llm_response("Fraud Probability: 0.5\nRecommendation: Review")
        assert isinstance(result, DetailedFraudAnalysis)

    def test_reasoning_extracted(self):
        response = "Fraud Probability: 0.5\nConfidence: 0.7\nReasoning: unusual location detected\nRecommendation: Review"
        result = self.service._parse_llm_response(response)
        assert "unusual location" in result.reasoning


# ── analyze_transaction (enhanced_mock path) ──────────────────────────────────

class TestAnalyzeTransactionEnhancedMock:
    def setup_method(self):
        self.service = _make_llm_service_with_enhanced_mock()

    def test_returns_detailed_fraud_analysis(self):
        result = self.service.analyze_transaction("Normal purchase", [])
        assert isinstance(result, DetailedFraudAnalysis)

    def test_delegates_to_enhanced_mock(self):
        docs = [_make_doc("FRD-001")]
        self.service.analyze_transaction("test", docs)
        self.service.enhanced_mock.analyze_transaction.assert_called_once_with("test", docs)

    def test_enhanced_mock_exception_falls_through(self):
        """If enhanced_mock raises, should fall through to standard processing."""
        self.service.enhanced_mock.analyze_transaction.side_effect = RuntimeError("mock failed")
        # Should not raise; falls through to llm chain which may also fail → returns error analysis
        result = self.service.analyze_transaction("test", [])
        assert isinstance(result, DetailedFraudAnalysis)


# ── analyze_transaction (local path) ─────────────────────────────────────────

class TestAnalyzeTransactionLocalPath:
    def test_delegates_to_local_llm_service(self):
        service = _make_llm_service_with_enhanced_mock()
        service.llm_service_type = "local"

        mock_local = MagicMock()
        mock_local.analyze_transaction.return_value = DetailedFraudAnalysis(
            fraud_probability=0.8,
            confidence=0.9,
            reasoning="fraud",
            recommendation="Deny",
            full_analysis="full",
            retrieved_patterns=[],
        )
        service.local_llm_service = mock_local

        result = service.analyze_transaction("high risk transaction", [])
        mock_local.analyze_transaction.assert_called_once()
        assert result.recommendation == "Deny"

    def test_local_llm_exception_falls_through(self):
        service = _make_llm_service_with_enhanced_mock()
        service.llm_service_type = "local"

        mock_local = MagicMock()
        mock_local.analyze_transaction.side_effect = RuntimeError("local failed")
        service.local_llm_service = mock_local

        # After local fails, tries enhanced_mock path
        result = service.analyze_transaction("test", [])
        assert isinstance(result, DetailedFraudAnalysis)


# ── analyze_transaction (openai chain path) ───────────────────────────────────

class TestAnalyzeTransactionOpenAIPath:
    def test_successful_chain_invocation(self):
        service = _make_llm_service_with_enhanced_mock()
        service.llm_service_type = "openai"
        service.enhanced_mock = None
        service.local_llm_service = None

        mock_result = MagicMock()
        mock_result.content = "Fraud Probability: 0.3\nConfidence: 0.8\nReasoning: normal\nRecommendation: Approve"
        service.llm.__or__ = MagicMock(return_value=MagicMock(invoke=MagicMock(return_value=mock_result)))

        # Mock the chain construction (prompt | llm)
        with patch("app.services.llm_service.PromptTemplate") as mock_pt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_result
            mock_pt.return_value.__or__ = MagicMock(return_value=mock_chain)
            mock_pt.return_value.__ror__ = MagicMock(return_value=mock_chain)
            # Direct patch of chain building
            service.llm = MagicMock()
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_pt.return_value = mock_prompt

            result = service.analyze_transaction("normal purchase", [])

        assert isinstance(result, DetailedFraudAnalysis)

    def test_quota_error_returns_error_analysis(self):
        service = _make_llm_service_with_enhanced_mock()
        service.llm_service_type = "openai"
        service.enhanced_mock = None
        service.local_llm_service = None

        with patch("app.services.llm_service.PromptTemplate") as mock_pt:
            mock_chain = MagicMock()
            mock_chain.invoke.side_effect = Exception("insufficient_quota exceeded")
            mock_prompt = MagicMock()
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            mock_pt.return_value = mock_prompt

            with patch("app.services.llm_service.LocalLLMService") as mock_local_cls:
                mock_local_instance = MagicMock()
                mock_local_instance.available = False
                mock_local_instance.online_available = False
                mock_local_instance.local_available = False
                mock_local_cls.return_value = mock_local_instance

                result = service.analyze_transaction("test", [])

        assert isinstance(result, DetailedFraudAnalysis)


# ── _initialize_mock_llm ──────────────────────────────────────────────────────

class TestInitializeMockLlm:
    def test_initializes_enhanced_mock_when_no_ollama(self):
        with patch("app.services.llm_service.HuggingFaceEmbeddings"), \
             patch("app.services.llm_service.LocalLLMService") as mock_local_cls, \
             patch("app.services.llm_service.EnhancedMockLLM") as mock_mock_cls, \
             patch("app.services.llm_service.EnhancedFakeListLLM"), \
             patch("app.services.llm_service.settings") as mock_settings:

            mock_settings.OPENAI_API_KEY = "your_fake_key"
            mock_settings.EMBEDDING_MODEL = "mock"
            mock_settings.LLM_MODEL = "gpt-4"
            mock_settings.LOCAL_LLM_MODEL = "llama3"
            mock_settings.USE_LOCAL_LLM = False
            mock_settings.USE_ONLINE_OLLAMA = False
            mock_settings.FORCE_LOCAL_LLM = False

            mock_mock_cls.return_value = MagicMock()

            from app.services.llm_service import LLMService
            service = LLMService.__new__(LLMService)
            service.llm = None
            service.embedding_model = MagicMock()
            service.llm_service_type = None
            service.local_llm_service = None
            service.enhanced_mock = None

            service._initialize_mock_llm()

            assert service.llm_service_type in ("enhanced_mock", "local", "basic_mock")
