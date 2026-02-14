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

    SYSTEM_CONTEXT = (
        "Du bist ein hilfreicher Assistent der Nutzern Chats antwortet. "
        "Antworte immer auf deutsch und verwende keine Textformatierung außer Zeilenumbrüchen. "
        "Antworte in maximal 400 Wörtern."
    )

    async def generate_response(self, prompt: str) -> str:
        """Generate response from Ollama model"""
        try:
            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "system": self.SYSTEM_CONTEXT,
            }

            async def _make_request():
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=payload, timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get(
                                "response", "Sorry, I could not generate a response."
                            )
                        else:
                            self.logger.error(f"Ollama API error: {response.status}")
                            return "Sorry, I'm having trouble connecting to my AI brain right now."

            return await asyncio.wait_for(_make_request(), timeout=120)

        except asyncio.TimeoutError:
            self.logger.error("Ollama request timed out")
            return "Sorry, my response took too long to generate. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while generating a response."

    async def generate_response_background(self, prompt: str) -> str:
        """Generate response from Ollama model in a separate thread to avoid blocking"""
        return await asyncio.to_thread(self._generate_response_sync, prompt)

    def _generate_response_sync(self, prompt: str) -> str:
        """Synchronous wrapper for generating response in executor"""
        try:
            import requests

            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "system": self.SYSTEM_CONTEXT,
            }

            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Sorry, I could not generate a response.")
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return "Sorry, I'm having trouble connecting to my AI brain right now."

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while generating a response."

    async def stream_response(self, prompt: str, callback):
        """Stream response from Ollama model and call callback with each chunk"""
        try:
            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": True,
                "system": self.SYSTEM_CONTEXT,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    if response.status == 200:
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    data = line.decode("utf-8").strip()
                                    if data:
                                        import json

                                        json_data = json.loads(data)
                                        if "response" in json_data:
                                            chunk = json_data["response"]
                                            if chunk:
                                                full_response += chunk
                                                await callback(chunk)
                                except Exception:
                                    continue
                        return (
                            full_response
                            if full_response
                            else "Sorry, I could not generate a response."
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
