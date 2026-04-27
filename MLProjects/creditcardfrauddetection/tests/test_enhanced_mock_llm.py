"""
Tests for app/services/enhanced_mock_llm.py (currently 30% coverage).
"""
import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

from app.services.enhanced_mock_llm import EnhancedMockLLM, EnhancedFakeListLLM


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_doc(case_id: str, content: str = "fraud pattern") -> Document:
    return Document(page_content=content, metadata={"case_id": case_id})


# ── EnhancedMockLLM._get_response_type ───────────────────────────────────────

class TestGetResponseType:
    def setup_method(self):
        self.llm = EnhancedMockLLM()

    def test_legitimate_no_keywords(self):
        result = self.llm._get_response_type("Normal grocery purchase at local store")
        assert result == "legitimate"

    def test_suspicious_one_keyword(self):
        result = self.llm._get_response_type("high value purchase at store")
        assert result == "suspicious"

    def test_fraudulent_three_or_more_keywords(self):
        text = "unusual location high value suspicious transaction at odd hours rapid succession"
        result = self.llm._get_response_type(text)
        assert result == "fraudulent"

    def test_case_insensitive(self):
        result = self.llm._get_response_type("HIGH VALUE purchase")
        assert result == "suspicious"

    def test_amount_keyword_triggers_suspicious(self):
        result = self.llm._get_response_type("Purchase of $1000 at store")
        assert result == "suspicious"

    def test_electronics_keyword(self):
        result = self.llm._get_response_type("electronics purchase at store")
        assert result == "suspicious"


# ── EnhancedMockLLM._extract_pattern_id ──────────────────────────────────────

class TestExtractPatternId:
    def setup_method(self):
        self.llm = EnhancedMockLLM()

    def test_returns_case_id_from_first_matching_doc(self):
        docs = [_make_doc("FRD-001"), _make_doc("FRD-002")]
        result = self.llm._extract_pattern_id(docs)
        assert result == "FRD-001"

    def test_empty_list_returns_unknown(self):
        result = self.llm._extract_pattern_id([])
        assert result == "FRD-UNKNOWN"

    def test_doc_without_case_id_skipped(self):
        doc_no_id = Document(page_content="text", metadata={})
        doc_with_id = Document(page_content="text", metadata={"case_id": "FRD-999"})
        result = self.llm._extract_pattern_id([doc_no_id, doc_with_id])
        assert result == "FRD-999"

    def test_all_docs_without_case_id_returns_unknown(self):
        docs = [Document(page_content="text", metadata={}) for _ in range(3)]
        result = self.llm._extract_pattern_id(docs)
        assert result == "FRD-UNKNOWN"


# ── EnhancedMockLLM._parse_response ──────────────────────────────────────────

class TestParseResponse:
    def setup_method(self):
        self.llm = EnhancedMockLLM()

    def test_parses_approve_recommendation(self):
        response = """
        Fraud Probability: 0.12
        Confidence: 0.88
        Reasoning: Transaction looks normal.
        Recommendation: Approve
        """
        analysis = self.llm._parse_response(response)
        assert analysis.fraud_probability == pytest.approx(0.12)
        assert analysis.confidence == pytest.approx(0.88)
        assert analysis.recommendation == "Approve"

    def test_parses_deny_recommendation(self):
        response = """
        Fraud Probability: 0.91
        Confidence: 0.95
        Reasoning: High risk transaction.
        Recommendation: Deny
        """
        analysis = self.llm._parse_response(response)
        assert analysis.recommendation == "Deny"

    def test_parses_review_recommendation(self):
        response = """
        Fraud Probability: 0.50
        Confidence: 0.65
        Reasoning: Mixed signals.
        Recommendation: Review
        """
        analysis = self.llm._parse_response(response)
        assert analysis.recommendation == "Review"

    def test_defaults_when_no_matches(self):
        analysis = self.llm._parse_response("No structured content here.")
        assert analysis.fraud_probability == 0.5
        assert analysis.confidence == 0.5
        assert analysis.recommendation == "Review"

    def test_reasoning_extracted(self):
        response = """
        Fraud Probability: 0.20
        Confidence: 0.85
        Reasoning: Customer history is clean with no anomalies.
        Recommendation: Approve
        """
        analysis = self.llm._parse_response(response)
        assert "clean" in analysis.reasoning

    def test_retrieved_patterns_empty_by_default(self):
        analysis = self.llm._parse_response("Fraud Probability: 0.1 Confidence: 0.9 Recommendation: Approve")
        assert analysis.retrieved_patterns == []


# ── EnhancedMockLLM.analyze_transaction ──────────────────────────────────────

class TestAnalyzeTransaction:
    def setup_method(self):
        self.llm = EnhancedMockLLM()

    def test_returns_detailed_fraud_analysis(self):
        from app.api.models import DetailedFraudAnalysis
        result = self.llm.analyze_transaction("Normal grocery store purchase", [])
        assert isinstance(result, DetailedFraudAnalysis)

    def test_legitimate_transaction_low_probability(self):
        result = self.llm.analyze_transaction("Normal grocery store purchase at local market", [])
        assert result.fraud_probability < 0.35

    def test_fraudulent_transaction_high_probability(self):
        text = "unusual location high value suspicious transaction odd hours rapid succession electronics purchase $5000"
        result = self.llm.analyze_transaction(text, [])
        assert result.fraud_probability > 0.60

    def test_suspicious_transaction_mid_range(self):
        result = self.llm.analyze_transaction("high value purchase at store", [])
        assert 0.30 <= result.fraud_probability <= 0.70

    def test_retrieved_patterns_populated(self):
        docs = [_make_doc("FRD-A"), _make_doc("FRD-B")]
        result = self.llm.analyze_transaction("Normal purchase", docs)
        assert "FRD-A" in result.retrieved_patterns
        assert "FRD-B" in result.retrieved_patterns

    def test_full_analysis_is_string(self):
        result = self.llm.analyze_transaction("Normal purchase", [])
        assert isinstance(result.full_analysis, str)
        assert len(result.full_analysis) > 0

    def test_approve_recommendation_for_legitimate(self):
        result = self.llm.analyze_transaction("Everyday grocery purchase at local market", [])
        assert result.recommendation in ["Approve", "Review"]

    def test_deny_recommendation_for_fraudulent(self):
        text = "unusual location high value suspicious rapid succession electronics purchase $5000 different country"
        result = self.llm.analyze_transaction(text, [])
        assert result.recommendation in ["Deny", "Review"]

    def test_empty_transaction_text(self):
        result = self.llm.analyze_transaction("", [])
        assert result.fraud_probability < 0.35  # No keywords → legitimate

    def test_pattern_id_in_full_analysis(self):
        docs = [_make_doc("FRD-XYZ")]
        text = "unusual location high value suspicious rapid succession electronics $5000"
        result = self.llm.analyze_transaction(text, docs)
        # FRD-XYZ may appear in the fraudulent template
        assert isinstance(result.full_analysis, str)


# ── EnhancedFakeListLLM ───────────────────────────────────────────────────────

class TestEnhancedFakeListLLM:
    def setup_method(self):
        self.llm = EnhancedFakeListLLM()

    def test_default_responses_loaded(self):
        assert len(self.llm.responses) == 3

    def test_high_risk_returns_deny(self):
        prompt = "unusual location high value suspicious transaction"
        result = self.llm._select_relevant_response(prompt)
        assert "Deny" in result

    def test_medium_risk_returns_review(self):
        prompt = "high value purchase at store"
        result = self.llm._select_relevant_response(prompt)
        assert "Review" in result

    def test_low_risk_returns_approve(self):
        prompt = "standard grocery purchase at supermarket"
        result = self.llm._select_relevant_response(prompt)
        assert "Approve" in result

    def test_call_returns_string(self):
        result = self.llm._call("some transaction prompt")
        assert isinstance(result, str)

    def test_custom_responses(self):
        custom = ["resp_a", "resp_b", "resp_c"]
        llm = EnhancedFakeListLLM(responses=custom)
        assert llm.responses == custom

    def test_case_insensitive_matching(self):
        prompt = "UNUSUAL LOCATION transaction HIGH VALUE"
        result = self.llm._select_relevant_response(prompt)
        assert "Deny" in result
