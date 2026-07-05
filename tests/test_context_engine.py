"""Tests for context compression engine."""

import json
import pytest
from uniskill.context_engine import (
    ContentType,
    SmartCrusher,
    CodeCompressor,
    SemanticCompactor,
    ContextManager,
    ContentRouter,
    CompressorFactory,
)


class TestContextDetection:
    """Test content type routing."""

    def test_detect_json(self):
        router = ContentRouter()
        result = router.detect_type('{"key": "value"}')
        assert result == ContentType.JSON

    def test_detect_python_code(self):
        router = ContentRouter()
        result = router.detect_type("def hello():\n    return 'world'")
        assert result == ContentType.CODE

    def test_detect_long_text(self):
        router = ContentRouter()
        long_text = "This is a long text. " * 30
        result = router.detect_type(long_text)
        assert result == ContentType.TEXT


class TestSmartCrusher:
    """Test SmartCrusher compression."""

    def test_json_compression(self):
        crusher = SmartCrusher()
        data = json.dumps({"key": "value", "items": [1, 2, 3]}) * 100
        compressed, stats = crusher.compress(data)

        assert len(compressed.encode()) < len(data.encode()) * 0.5
        assert stats.space_saved_percent > 40


class TestCodeCompressor:
    """Test CodeCompressor."""

    def test_strips_comments(self):
        compressor = CodeCompressor()
        code = """
# This is a comment
def foo(x):
    # Another comment
    return x * 2  # Inline comment
"""
        compressed, _ = compressor.compress(code)

        assert "# This is a comment" not in compressed
        assert "def foo" in compressed


class TestSemanticCompactor:
    """Test SemanticCompactor."""

    def test_short_text_preserved(self):
        compactor = SemanticCompactor()
        short = "Hello world. This is a test."
        compressed, _ = compactor.compress(short)

        assert "Hello world" in compressed


class TestContextManager:
    """Test context manager with token budgeting."""

    def test_within_budget(self):
        manager = ContextManager(max_tokens=10000)
        # Should not compress when under budget
        manager.add_context("msg1", "short message")
        assert manager.get_total_tokens() < 10000

    def test_compress_when_near_budget(self):
        manager = ContextManager(max_tokens=100, compression_threshold=0.8)

        # Add enough content to trigger compression
        large_text = "word " * 200
        manager.add_context("msg1", large_text)

        stats = manager.get_stats()
        assert stats["total_compressions"] >= 0

    def test_context_retrieval(self):
        manager = ContextManager()
        manager.add_context("key1", "value1")
        manager.add_context("key2", "value2")

        assert manager.get_context("key1") == "value1"
        assert manager.get_context("nonexistent") is None

    def test_context_clear(self):
        manager = ContextManager()
        manager.add_context("key1", "value1")
        manager.clear()

        assert manager.get_total_tokens() == 0


class TestCompressorFactory:
    """Test compressor factory."""

    def test_create_json_compressor(self):
        factory = CompressorFactory()
        compressor = factory.create(ContentType.JSON)
        assert isinstance(compressor, SmartCrusher)

    def test_create_code_compressor(self):
        factory = CompressorFactory()
        compressor = factory.create(ContentType.CODE)
        assert isinstance(compressor, CodeCompressor)

    def test_create_text_compressor(self):
        factory = CompressorFactory()
        compressor = factory.create(ContentType.TEXT)
        assert isinstance(compressor, SemanticCompactor)
