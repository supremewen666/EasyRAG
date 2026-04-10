"""Tests for model configuration helpers."""

from __future__ import annotations

import os
import unittest

from easyrag.config import (
    get_embedding_base_url,
    get_embedding_model_name,
    get_kg_base_url,
    get_kg_entity_types,
    get_kg_model_name,
    get_model_name,
    get_openai_base_url,
    get_query_base_url,
    get_query_model_name,
    get_rerank_base_url,
    get_rerank_model_name,
)


class ConfigTestCase(unittest.TestCase):
    """Verify provider-agnostic model config behavior."""

    def test_model_name_defaults_from_model_identifier(self) -> None:
        old_model = os.environ.get("EASYRAG_MODEL")
        old_name = os.environ.get("EASYRAG_MODEL_NAME")
        os.environ["EASYRAG_MODEL"] = "openai:gpt-4.1-mini"
        os.environ.pop("EASYRAG_MODEL_NAME", None)
        try:
            self.assertEqual(get_model_name(), "gpt-4.1-mini")
        finally:
            if old_model is None:
                os.environ.pop("EASYRAG_MODEL", None)
            else:
                os.environ["EASYRAG_MODEL"] = old_model
            if old_name is None:
                os.environ.pop("EASYRAG_MODEL_NAME", None)
            else:
                os.environ["EASYRAG_MODEL_NAME"] = old_name

    def test_openai_base_url_can_be_set_for_compatible_provider(self) -> None:
        old_value = os.environ.get("OPENAI_BASE_URL")
        os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com/v1"
        try:
            self.assertEqual(get_openai_base_url(), "https://api.deepseek.com/v1")
        finally:
            if old_value is None:
                os.environ.pop("OPENAI_BASE_URL", None)
            else:
                os.environ["OPENAI_BASE_URL"] = old_value

    def test_role_specific_model_names_default_and_override(self) -> None:
        old_query = os.environ.get("EASYRAG_QUERY_MODEL_NAME")
        old_embed = os.environ.get("EASYRAG_EMBEDDING_MODEL_NAME")
        old_kg = os.environ.get("EASYRAG_KG_MODEL_NAME")
        old_rerank = os.environ.get("EASYRAG_RERANK_MODEL_NAME")
        os.environ["EASYRAG_MODEL_NAME"] = "gpt-4.1-mini"
        os.environ["EASYRAG_QUERY_MODEL_NAME"] = "qwen3-query"
        os.environ.pop("EASYRAG_KG_MODEL_NAME", None)
        os.environ.pop("EASYRAG_EMBEDDING_MODEL_NAME", None)
        os.environ.pop("EASYRAG_RERANK_MODEL_NAME", None)
        try:
            self.assertEqual(get_query_model_name(), "qwen3-query")
            self.assertEqual(get_kg_model_name(), "qwen3-query")
            self.assertEqual(get_embedding_model_name(), "qwen3-embedding")
            self.assertEqual(get_rerank_model_name(), "qwen3-rerank")
        finally:
            if old_query is None:
                os.environ.pop("EASYRAG_QUERY_MODEL_NAME", None)
            else:
                os.environ["EASYRAG_QUERY_MODEL_NAME"] = old_query
            if old_kg is None:
                os.environ.pop("EASYRAG_KG_MODEL_NAME", None)
            else:
                os.environ["EASYRAG_KG_MODEL_NAME"] = old_kg
            if old_embed is None:
                os.environ.pop("EASYRAG_EMBEDDING_MODEL_NAME", None)
            else:
                os.environ["EASYRAG_EMBEDDING_MODEL_NAME"] = old_embed
            if old_rerank is None:
                os.environ.pop("EASYRAG_RERANK_MODEL_NAME", None)
            else:
                os.environ["EASYRAG_RERANK_MODEL_NAME"] = old_rerank

    def test_role_specific_base_urls_fall_back_to_shared_base_url(self) -> None:
        old_openai = os.environ.get("OPENAI_BASE_URL")
        old_query = os.environ.get("EASYRAG_QUERY_BASE_URL")
        old_embed = os.environ.get("EASYRAG_EMBEDDING_BASE_URL")
        old_kg = os.environ.get("EASYRAG_KG_BASE_URL")
        old_rerank = os.environ.get("EASYRAG_RERANK_BASE_URL")
        os.environ["OPENAI_BASE_URL"] = "https://api.example.com/v1"
        os.environ["EASYRAG_QUERY_BASE_URL"] = "https://query.example.com/v1"
        os.environ.pop("EASYRAG_EMBEDDING_BASE_URL", None)
        os.environ.pop("EASYRAG_KG_BASE_URL", None)
        os.environ.pop("EASYRAG_RERANK_BASE_URL", None)
        try:
            self.assertEqual(get_query_base_url(), "https://query.example.com/v1")
            self.assertEqual(get_kg_base_url(), "https://api.example.com/v1")
            self.assertEqual(get_embedding_base_url(), "https://api.example.com/v1")
            self.assertEqual(get_rerank_base_url(), "https://api.example.com/v1")
        finally:
            if old_openai is None:
                os.environ.pop("OPENAI_BASE_URL", None)
            else:
                os.environ["OPENAI_BASE_URL"] = old_openai
            if old_query is None:
                os.environ.pop("EASYRAG_QUERY_BASE_URL", None)
            else:
                os.environ["EASYRAG_QUERY_BASE_URL"] = old_query
            if old_kg is None:
                os.environ.pop("EASYRAG_KG_BASE_URL", None)
            else:
                os.environ["EASYRAG_KG_BASE_URL"] = old_kg
            if old_embed is None:
                os.environ.pop("EASYRAG_EMBEDDING_BASE_URL", None)
            else:
                os.environ["EASYRAG_EMBEDDING_BASE_URL"] = old_embed
            if old_rerank is None:
                os.environ.pop("EASYRAG_RERANK_BASE_URL", None)
            else:
                os.environ["EASYRAG_RERANK_BASE_URL"] = old_rerank

    def test_kg_entity_types_can_be_configured(self) -> None:
        old_value = os.environ.get("EASYRAG_KG_ENTITY_TYPES")
        os.environ["EASYRAG_KG_ENTITY_TYPES"] = "component, module ,workflow"
        try:
            self.assertEqual(get_kg_entity_types(), ("component", "module", "workflow"))
        finally:
            if old_value is None:
                os.environ.pop("EASYRAG_KG_ENTITY_TYPES", None)
            else:
                os.environ["EASYRAG_KG_ENTITY_TYPES"] = old_value


if __name__ == "__main__":
    unittest.main()
