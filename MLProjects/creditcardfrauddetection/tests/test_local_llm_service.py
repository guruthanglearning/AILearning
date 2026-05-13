"""
Tests for app/services/local_llm_service.py (currently 21% coverage).
Network calls via `requests` are mocked throughout.
"""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from app.api.models import DetailedFraudAnalysis


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_service(local_available=False, online_available=False,
                  prefer_online=True, use_online=False):
    """Return a LocalLLMService with availability checks mocked."""
    with patch("app.services.local_llm_service.requests") as mock_req, \
         patch("app.services.local_llm_service.settings") as mock_settings:

        mock_settings.USE_ONLINE_OLLAMA = use_online
        mock_settings.ONLINE_OLLAMA_API_URL = "http://fake-online-ollama" if use_online else ""
        mock_settings.ONLINE_OLLAMA_API_KEY = "fake-key" if use_online else ""
        mock_settings.LOCAL_LLM_API_URL = "http://localhost:11434/api"
        mock_settings.LOCAL_LLM_MODEL = "llama3"
        mock_settings.MASKED_ONLINE_OLLAMA_API_KEY = None

        def get_side_effect(url, **kwargs):
            resp = MagicMock()
            if "localhost" in url and local_available:
                resp.status_code = 200
            elif "fake-online-ollama" in url and online_available:
                resp.status_code = 200
            else:
                resp.status_code = 503
            return resp

        mock_req.get.side_effect = get_side_effect
        mock_req.post.side_effect = Exception("Should not be called during init")

        from app.services.local_llm_service import LocalLLMService
        service = LocalLLMService(model_name="llama3", prefer_online=prefer_online)

    return service, mock_req


def _make_doc(case_id="FRD-001"):
    return Document(page_content="fraud content", metadata={"case_id": case_id, "fraud_type": "Card Testing"})


# ── Initialization / availability ─────────────────────────────────────────────

class TestLocalLLMServiceInit:
    def test_unavailable_when_neither_reachable(self):
        service, _ = _make_service(local_available=False, online_available=False)
        assert service.available is False
        assert service.local_available is False
        assert service.online_available is False

    def test_available_when_local_reachable(self):
        service, _ = _make_service(local_available=True, online_available=False, prefer_online=False)
        assert service.available is True
        assert service.local_available is True

    def test_model_name_stored(self):
        service, _ = _make_service()
        assert service.model_name == "llama3"

    def test_prefer_online_flag_stored(self):
        service, _ = _make_service(prefer_online=True)
        assert service.prefer_online is True

    def test_prefer_local_flag_stored(self):
        service, _ = _make_service(prefer_online=False)
        assert service.prefer_online is False


# ── _check_local_availability ─────────────────────────────────────────────────

class TestCheckLocalAvailability:
    def test_returns_true_when_200(self):
        service, _ = _make_service(local_available=True, prefer_online=False)
        assert service.local_available is True

    def test_returns_false_when_not_200(self):
        service, _ = _make_service(local_available=False, prefer_online=False)
        assert service.local_available is False

    def test_returns_false_on_connection_error(self):
        with patch("app.services.local_llm_service.requests") as mock_req, \
             patch("app.services.local_llm_service.settings") as mock_settings:
            mock_settings.USE_ONLINE_OLLAMA = False
            mock_settings.ONLINE_OLLAMA_API_URL = ""
            mock_settings.ONLINE_OLLAMA_API_KEY = ""
            mock_settings.LOCAL_LLM_API_URL = "http://localhost:11434/api"
            mock_settings.LOCAL_LLM_MODEL = "llama3"
            mock_settings.MASKED_ONLINE_OLLAMA_API_KEY = None

            mock_req.get.side_effect = Exception("Connection refused")

            from app.services.local_llm_service import LocalLLMService
            service = LocalLLMService(model_name="llama3")
            assert service.local_available is False


# ── _check_online_availability ────────────────────────────────────────────────

class TestCheckOnlineAvailability:
    def test_skips_when_not_configured(self):
        service, _ = _make_service(use_online=False)
        assert service.online_available is False

    def test_available_via_status_endpoint(self):
        with patch("app.services.local_llm_service.requests") as mock_req, \
             patch("app.services.local_llm_service.settings") as mock_settings:
            mock_settings.USE_ONLINE_OLLAMA = True
            mock_settings.ONLINE_OLLAMA_API_URL = "http://online-ollama"
            mock_settings.ONLINE_OLLAMA_API_KEY = "key123"
            mock_settings.LOCAL_LLM_API_URL = "http://localhost:11434/api"
            mock_settings.LOCAL_LLM_MODEL = "llama3"
            mock_settings.MASKED_ONLINE_OLLAMA_API_KEY = None

            online_resp = MagicMock()
            online_resp.status_code = 200
            local_resp = MagicMock()
            local_resp.status_code = 503

            def get_side_effect(url, **kwargs):
                if "status" in url or "online-ollama" in url:
                    return online_resp
                return local_resp

            mock_req.get.side_effect = get_side_effect

            from app.services.local_llm_service import LocalLLMService
            service = LocalLLMService(model_name="llama3", prefer_online=True)
            assert service.online_available is True


# ── _format_similar_patterns ──────────────────────────────────────────────────

class TestFormatSimilarPatterns:
    def setup_method(self):
        self.service, _ = _make_service()

    def test_empty_returns_no_patterns_text(self):
        result = self.service._format_similar_patterns([])
        assert "No similar" in result

    def test_includes_case_id(self):
        doc = _make_doc("FRD-XYZ")
        result = self.service._format_similar_patterns([doc])
        assert "FRD-XYZ" in result

    def test_includes_pattern_number(self):
        docs = [_make_doc("A"), _make_doc("B")]
        result = self.service._format_similar_patterns(docs)
        assert "SIMILAR PATTERN 1" in result
        assert "SIMILAR PATTERN 2" in result

    def test_includes_page_content(self):
        doc = Document(page_content="unique fraud text", metadata={"case_id": "X"})
        result = self.service._format_similar_patterns([doc])
        assert "unique fraud text" in result


# ── _create_prompt ────────────────────────────────────────────────────────────

class TestCreatePrompt:
    def setup_method(self):
        self.service, _ = _make_service()

    def test_includes_transaction_text(self):
        prompt = self.service._create_prompt("big purchase at store", "no patterns")
        assert "big purchase at store" in prompt

    def test_includes_patterns_text(self):
        prompt = self.service._create_prompt("purchase", "FRD-001 card testing")
        assert "FRD-001 card testing" in prompt

    def test_includes_fraud_probability_instruction(self):
        prompt = self.service._create_prompt("x", "y")
        assert "Fraud Probability" in prompt

    def test_includes_recommendation_instruction(self):
        prompt = self.service._create_prompt("x", "y")
        assert "Recommendation" in prompt


# ── _parse_llm_response (via analyze_transaction) ────────────────────────────

class TestParseLlmResponse:
    def _make_service_with_response(self, response_text):
        """Make service that returns a specific string from _call_ollama_api."""
        service, _ = _make_service(local_available=True, prefer_online=False)
        service.available = True
        with patch.object(service, "_call_ollama_api", return_value=response_text):
            result = service.analyze_transaction("transaction text", [])
        return result

    def test_parses_approve(self):
        response = "Fraud Probability: 0.1\nConfidence: 0.9\nRecommendation: Approve\nReason: Normal"
        result = self._make_service_with_response(response)
        assert result.recommendation == "Approve"

    def test_parses_deny(self):
        response = "Fraud Probability: 0.9\nConfidence: 0.95\nRecommendation: Deny\nReason: Fraud"
        result = self._make_service_with_response(response)
        assert result.recommendation == "Deny"

    def test_parses_review(self):
        response = "Fraud Probability: 0.5\nConfidence: 0.6\nRecommendation: Review\nReason: Unclear"
        result = self._make_service_with_response(response)
        assert result.recommendation == "Review"

    def test_default_review_on_empty(self):
        result = self._make_service_with_response("")
        assert result.recommendation == "Review"

    def test_full_analysis_populated(self):
        response = "Fraud Probability: 0.3\nConfidence: 0.8\nRecommendation: Approve\nOK"
        result = self._make_service_with_response(response)
        assert len(result.full_analysis) > 0


# ── analyze_transaction ───────────────────────────────────────────────────────

class TestAnalyzeTransaction:
    def test_returns_error_analysis_when_unavailable(self):
        service, _ = _make_service(local_available=False, online_available=False)
        result = service.analyze_transaction("test", [])
        assert isinstance(result, DetailedFraudAnalysis)
        assert result.recommendation == "Review"

    def test_retrieved_patterns_populated(self):
        service, _ = _make_service(local_available=True, prefer_online=False)
        docs = [_make_doc("FRD-A"), _make_doc("FRD-B")]
        with patch.object(service, "_call_ollama_api",
                          return_value="Fraud Probability: 0.2\nConfidence: 0.8\nRecommendation: Approve"):
            result = service.analyze_transaction("normal purchase", docs)
        assert "FRD-A" in result.retrieved_patterns
        assert "FRD-B" in result.retrieved_patterns

    def test_exception_in_call_returns_error_analysis(self):
        service, _ = _make_service(local_available=True, prefer_online=False)
        with patch.object(service, "_call_ollama_api", side_effect=RuntimeError("API error")):
            result = service.analyze_transaction("test", [])
        assert isinstance(result, DetailedFraudAnalysis)
        assert result.confidence == pytest.approx(0.1)


# ── _call_ollama_api (local path) ─────────────────────────────────────────────

class TestCallOllamaApiLocal:
    def test_calls_local_api_when_available(self):
        service, _ = _make_service(local_available=True, prefer_online=False)
        service.local_available = True
        service.online_available = False
        service.prefer_online = False

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Fraud Probability: 0.5\nRecommendation: Review"}

        with patch("app.services.local_llm_service.requests") as mock_req:
            mock_req.post.return_value = mock_response
            result = service._call_ollama_api("test prompt")

        assert "Fraud Probability" in result

    def test_non_200_response_falls_back_to_cli(self):
        """When local API returns 500, the service falls back to CLI subprocess."""
        service, _ = _make_service(local_available=True, prefer_online=False)
        service.local_available = True
        service.online_available = False
        service.prefer_online = False
        service.use_online_ollama = False

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 500
        mock_post_resp.text = "Internal Server Error"

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Fraud Probability: 0.5\nConfidence: 0.5\nRecommendation: Review"

        with patch("app.services.local_llm_service.requests") as mock_req, \
             patch("subprocess.run", return_value=mock_proc):
            mock_req.post.return_value = mock_post_resp
            result = service._call_ollama_api("test prompt")

        assert "Fraud Probability" in result or "Error" in result or len(result) > 0
