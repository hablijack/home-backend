#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import logging
from library.Configuration import Configuration


class OllamaClient:
    def __init__(self):
        self.config = Configuration()
        self.logger = logging.getLogger("OLLAMA_CLIENT")
        self.host = self.config.ollama_host()
        self.model = self.config.ollama_model()

    async def generate_response(self, prompt: str) -> str:
        """Generate response from Ollama model"""
        try:
            url = f"{self.host}/api/generate"
            payload = {"model": self.model, "prompt": prompt, "stream": False}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get(
                            "response", "Sorry, I could not generate a response."
                        )
                    else:
                        self.logger.error(f"Ollama API error: {response.status}")
                        return "Sorry, I'm having trouble connecting to my AI brain right now."

        except asyncio.TimeoutError:
            self.logger.error("Ollama request timed out")
            return "Sorry, my response took too long to generate. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while generating a response."

    async def health_check(self) -> bool:
        """Check if Ollama service is available"""
        try:
            url = f"{self.host}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            return False
