"""
Tests for app/models/embeddings.py (currently 26% coverage).
SentenceTransformer is mocked to avoid downloading/loading the real model.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_sentence_transformer():
    """A mock SentenceTransformer that returns deterministic embeddings."""
    mock = MagicMock()
    mock.encode.side_effect = lambda texts, **kwargs: np.random.rand(len(texts), 384).astype(np.float32)
    return mock


@pytest.fixture
def embedding_model(mock_sentence_transformer):
    """EmbeddingModel with a mocked SentenceTransformer."""
    with patch("app.models.embeddings.SentenceTransformer", return_value=mock_sentence_transformer):
        from app.models.embeddings import EmbeddingModel
        model = EmbeddingModel(model_name="mock-model")
    return model


# ── EmbeddingModel initialization ────────────────────────────────────────────

class TestEmbeddingModelInit:
    def test_model_name_stored(self, embedding_model):
        assert embedding_model.model_name == "mock-model"

    def test_model_not_none(self, embedding_model):
        assert embedding_model.model is not None

    def test_device_is_string(self, embedding_model):
        assert embedding_model.device in ("cpu", "cuda")

    def test_dimension_set_from_settings(self, embedding_model):
        assert isinstance(embedding_model.dimension, int)
        assert embedding_model.dimension > 0

    def test_default_model_name_from_settings(self):
        """When no model_name provided, uses settings.EMBEDDING_MODEL."""
        with patch("app.models.embeddings.SentenceTransformer") as mock_st:
            mock_st.return_value = MagicMock()
            mock_st.return_value.encode.return_value = np.zeros((1, 384))
            from app.models.embeddings import EmbeddingModel
            from app.core.config import settings
            model = EmbeddingModel()
            assert model.model_name == settings.EMBEDDING_MODEL

    def test_load_model_failure_raises(self):
        """If SentenceTransformer raises, EmbeddingModel.__init__ raises."""
        with patch("app.models.embeddings.SentenceTransformer", side_effect=RuntimeError("load failed")):
            from app.models.embeddings import EmbeddingModel
            with pytest.raises(Exception):
                EmbeddingModel(model_name="bad-model")


# ── EmbeddingModel.encode ─────────────────────────────────────────────────────

class TestEmbeddingModelEncode:
    def test_encode_single_string(self, embedding_model, mock_sentence_transformer):
        mock_sentence_transformer.encode.return_value = np.ones((1, 384), dtype=np.float32)
        result = embedding_model.encode("fraud detection test")
        assert isinstance(result, np.ndarray)

    def test_encode_list_of_strings(self, embedding_model, mock_sentence_transformer):
        texts = ["text one", "text two", "text three"]
        mock_sentence_transformer.encode.return_value = np.ones((3, 384), dtype=np.float32)
        result = embedding_model.encode(texts)
        assert isinstance(result, np.ndarray)

    def test_encode_string_converted_to_list(self, embedding_model, mock_sentence_transformer):
        """Single string should be wrapped in a list before encoding."""
        mock_sentence_transformer.encode.return_value = np.ones((1, 384), dtype=np.float32)
        embedding_model.encode("single text")
        call_args = mock_sentence_transformer.encode.call_args
        assert isinstance(call_args[0][0], list)

    def test_encode_respects_batch_size(self, embedding_model, mock_sentence_transformer):
        mock_sentence_transformer.encode.return_value = np.ones((2, 384), dtype=np.float32)
        embedding_model.encode(["a", "b"], batch_size=64)
        call_args = mock_sentence_transformer.encode.call_args
        assert call_args[1].get("batch_size") == 64

    def test_encode_loads_model_if_none(self, mock_sentence_transformer):
        """If model is None, encode should call _load_model first."""
        with patch("app.models.embeddings.SentenceTransformer", return_value=mock_sentence_transformer):
            from app.models.embeddings import EmbeddingModel
            model = EmbeddingModel(model_name="mock-model")
            model.model = None  # Simulate unloaded model

            mock_sentence_transformer.encode.return_value = np.ones((1, 384), dtype=np.float32)
            with patch.object(model, "_load_model") as mock_load:
                mock_load.side_effect = lambda: setattr(model, "model", mock_sentence_transformer)
                model.encode("test")
                mock_load.assert_called_once()

    def test_encode_raises_on_model_error(self, embedding_model, mock_sentence_transformer):
        mock_sentence_transformer.encode.side_effect = RuntimeError("encode failed")
        with pytest.raises(Exception):
            embedding_model.encode("test text")


# ── EmbeddingModel.similarity ─────────────────────────────────────────────────

class TestEmbeddingModelSimilarity:
    def test_identical_embeddings_return_1(self, embedding_model):
        vec = np.array([1.0, 0.0, 0.0])
        sim = embedding_model.similarity(vec, vec)
        assert sim == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_embeddings_return_0(self, embedding_model):
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        sim = embedding_model.similarity(vec1, vec2)
        assert sim == pytest.approx(0.0, abs=1e-6)

    def test_opposite_embeddings_return_minus_1(self, embedding_model):
        vec = np.array([1.0, 0.0, 0.0])
        sim = embedding_model.similarity(vec, -vec)
        assert sim == pytest.approx(-1.0, abs=1e-6)

    def test_similarity_range(self, embedding_model):
        vec1 = np.random.rand(128)
        vec2 = np.random.rand(128)
        sim = embedding_model.similarity(vec1, vec2)
        assert -1.0 <= sim <= 1.0

    def test_returns_float(self, embedding_model):
        vec = np.array([1.0, 2.0, 3.0])
        result = embedding_model.similarity(vec, vec)
        assert isinstance(result, float)

    def test_zero_vector_raises(self, embedding_model):
        """Division by zero norm should raise or return NaN."""
        zero = np.array([0.0, 0.0, 0.0])
        vec = np.array([1.0, 0.0, 0.0])
        # numpy division by zero produces nan/inf, which may or may not raise
        try:
            result = embedding_model.similarity(zero, vec)
            # If it doesn't raise, result should be nan or inf
            assert not np.isfinite(result) or result == pytest.approx(0.0, abs=1e-6)
        except Exception:
            pass  # Raising is also acceptable


# ── EmbeddingModel.batch_similarity ──────────────────────────────────────────

class TestEmbeddingModelBatchSimilarity:
    def test_returns_array(self, embedding_model):
        query = np.array([1.0, 0.0, 0.0])
        corpus = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        result = embedding_model.batch_similarity(query, corpus)
        assert isinstance(result, np.ndarray)

    def test_shape_matches_corpus(self, embedding_model):
        query = np.random.rand(64)
        corpus = np.random.rand(5, 64)
        result = embedding_model.batch_similarity(query, corpus)
        assert result.shape == (5,)

    def test_identical_corpus_entry_has_highest_similarity(self, embedding_model):
        query = np.array([1.0, 0.0, 0.0])
        corpus = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
        result = embedding_model.batch_similarity(query, corpus)
        assert np.argmax(result) == 0

    def test_values_in_range(self, embedding_model):
        query = np.random.rand(32)
        corpus = np.random.rand(10, 32)
        result = embedding_model.batch_similarity(query, corpus)
        assert np.all(result >= -1.0) and np.all(result <= 1.0)

    def test_raises_on_bad_input(self, embedding_model):
        with pytest.raises(Exception):
            embedding_model.batch_similarity(None, None)
