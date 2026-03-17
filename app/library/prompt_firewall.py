#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Prompt Firewall - Vector-based security filter for user prompts.
Uses llama.cpp embeddings to detect harmful prompts via semantic similarity.
"""

import json
import logging
import os
import re
import aiohttp
import math
from typing import Optional
from dataclasses import dataclass
from library.Configuration import Configuration


@dataclass
class FirewallResult:
    """Result of firewall check."""

    allowed: bool
    category: Optional[str]
    severity: Optional[str]
    similarity: float
    matched_prompt: Optional[str]


class PromptFirewall:
    """Vector-based prompt firewall using llama.cpp embeddings."""

    DEFAULT_BLOCK_MESSAGE = (
        "Entschuldigung, aber diese Anfrage kann ich nicht bearbeiten. "
        "Sie ähnelt einer potenziell schädlichen oder missbräuchlichen Anfrage."
    )

    def __init__(self, config: Optional[Configuration] = None):
        self.logger = logging.getLogger("PROMPT_FIREWALL")
        self.config = config or Configuration()
        self.host = self.config.llama_host_nomic()
        self.embedding_model = "nomic-embed-text"
        self._disabled = self.config.prompt_firewall_disabled()

        if self._disabled:
            self.logger.warning("Prompt firewall is DISABLED via config")

        self._load_unsecure_prompts()
        self._unsecure_embeddings = {}
        self._embedding_cache_initialized = False

    def _load_unsecure_prompts(self):
        """Load unsecure prompts from JSON file."""
        config_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(config_dir, "prompt_firewall.json")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.unsecure_prompts = data.get("prompts", [])
            self.thresholds = data.get(
                "thresholds",
                {"critical": 0.7, "high": 0.75, "medium": 0.8, "low": 0.85},
            )
            self.logger.info(
                f"Loaded {len(self.unsecure_prompts)} unsecure prompt patterns"
            )

        except FileNotFoundError:
            self.logger.warning(f"Firewall config not found: {json_path}")
            self.unsecure_prompts = []
            self.thresholds = {
                "critical": 0.7,
                "high": 0.75,
                "medium": 0.8,
                "low": 0.85,
            }
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in firewall config: {e}")
            self.unsecure_prompts = []
            self.thresholds = {
                "critical": 0.7,
                "high": 0.75,
                "medium": 0.8,
                "low": 0.85,
            }

    async def _get_embedding(self, text: str) -> Optional[list]:
        """Get embedding vector for text using llama.cpp."""
        try:
            url = f"{self.host}/v1/embeddings"
            payload = {
                "model": self.embedding_model,
                "input": text,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        embedding = result.get("data", [{}])[0].get("embedding")
                        if embedding:
                            return embedding
                    else:
                        self.logger.warning(
                            f"Embedding API returned status {resp.status}"
                        )
                        return None
        except Exception as e:
            self.logger.error(f"Error getting embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def _initialize_embeddings(self):
        """Pre-compute embeddings for all unsecure prompts."""
        if self._embedding_cache_initialized:
            return

        self.logger.info("Initializing prompt firewall embeddings...")
        for unsecure in self.unsecure_prompts:
            text = unsecure["text"]
            if text not in self._unsecure_embeddings:
                embedding = await self._get_embedding(text)
                if embedding is not None:
                    self._unsecure_embeddings[text] = embedding
                    self.logger.debug(f"Cached embedding for: {text[:50]}...")
                else:
                    self.logger.warning(f"Could not get embedding for: {text[:50]}...")

        self._embedding_cache_initialized = True
        self.logger.info(f"Cached {len(self._unsecure_embeddings)} embeddings")

    async def check(self, prompt: str) -> FirewallResult:
        """
        Check if a prompt is secure.

        Args:
            prompt: The user prompt to check

        Returns:
            FirewallResult with allow/deny decision and details
        """
        if self._disabled:
            return FirewallResult(
                allowed=True,
                category=None,
                severity=None,
                similarity=0.0,
                matched_prompt=None,
            )

        if not self.unsecure_prompts:
            self.logger.warning("No unsecure prompts loaded, allowing all")
            return FirewallResult(
                allowed=True,
                category=None,
                severity=None,
                similarity=0.0,
                matched_prompt=None,
            )

        # Initialize embeddings on first run
        await self._initialize_embeddings()

        # Get embedding for user prompt
        prompt_embedding = await self._get_embedding(prompt)

        if prompt_embedding is None:
            # If we can't get embedding, use fallback heuristic
            self.logger.warning("Could not get embedding, using fallback check")
            return self._fallback_check(prompt)

        # Check similarity against all unsecure prompts (using cached embeddings)
        max_similarity = 0.0
        matched_category = None
        matched_severity = None
        matched_text = None

        if not self._unsecure_embeddings:
            self.logger.warning("No embeddings cached, using fallback check")
            return self._fallback_check(prompt)

        for unsecure in self.unsecure_prompts:
            text = unsecure["text"]
            unsecure_embedding = self._unsecure_embeddings.get(text)

            if unsecure_embedding is not None:
                similarity = self._cosine_similarity(
                    prompt_embedding, unsecure_embedding
                )

                if similarity > max_similarity:
                    max_similarity = similarity
                    matched_category = unsecure.get("category")
                    matched_severity = unsecure.get("severity", "high")
                    matched_text = text

        # Determine threshold based on severity
        threshold = self.thresholds.get(
            matched_severity, self.thresholds.get("high", 0.75)
        )

        if max_similarity >= threshold:
            self.logger.warning(
                f"Blocked prompt: similarity={max_similarity:.3f}, "
                f"category={matched_category}, severity={matched_severity}"
            )
            return FirewallResult(
                allowed=False,
                category=matched_category,
                severity=matched_severity,
                similarity=max_similarity,
                matched_prompt=matched_text,
            )

        self.logger.debug(
            f"Prompt allowed: max_similarity={max_similarity:.3f}, threshold={threshold}"
        )
        return FirewallResult(
            allowed=True,
            category=None,
            severity=None,
            similarity=max_similarity,
            matched_prompt=None,
        )

    def _fallback_check(self, prompt: str) -> FirewallResult:
        """Fallback synchronous check using keyword matching."""
        prompt_lower = prompt.lower()

        dangerous_patterns = {
            "ignore": ("system_abuse", "medium"),
            "forget": ("system_abuse", "medium"),
            "ignore all": ("jailbreak", "high"),
            "new rules": ("jailbreak", "high"),
            "you are now": ("jailbreak", "high"),
            "dan": ("jailbreak", "high"),
            "no restrictions": ("jailbreak", "high"),
            "build a bomb": ("harmful", "critical"),
            "create malware": ("harmful", "critical"),
            "hack into": ("harmful", "critical"),
            "phishing": ("social_engineering", "critical"),
            "steal credentials": ("social_engineering", "critical"),
            "ignoriere": ("system_abuse", "high"),
            "systemprompt": ("system_abuse", "high"),
            "vergiss": ("system_abuse", "medium"),
            "alle vorherigen": ("jailbreak", "high"),
            "keine regeln": ("jailbreak", "high"),
            "neue regeln": ("jailbreak", "high"),
            "du bist jetzt": ("jailbreak", "high"),
            "system-anweisung": ("system_abuse", "high"),
            "trainingsdaten": ("system_abuse", "medium"),
        }

        for pattern, (category, severity) in dangerous_patterns.items():
            if re.search(r"\b" + re.escape(pattern) + r"\b", prompt_lower):
                return FirewallResult(
                    allowed=False,
                    category=category,
                    severity=severity,
                    similarity=1.0,
                    matched_prompt=pattern,
                )

        return FirewallResult(
            allowed=True,
            category=None,
            severity=None,
            similarity=0.0,
            matched_prompt=None,
        )

    @property
    def block_message(self) -> str:
        """Get the message to show when a prompt is blocked."""
        return self.DEFAULT_BLOCK_MESSAGE
