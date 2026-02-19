import asyncio
import aiohttp
import logging
import time
from library.Configuration import Configuration


class OllamaClient:
    CONTEXT_TTL = 300  # 5 Minuten
    MAX_MESSAGES = 20  # Begrenzung gegen Token-Explosion

    SYSTEM_CONTEXT = (
        "Du bist ein hilfreicher Assistent der Nutzern Chats antwortet. "
        "Antworte immer auf deutsch und verwende keine Textformatierung außer Zeilenumbrüchen. "
        "Antworte in maximal 600 Wörtern."
    )

    def __init__(self):
        self.config = Configuration()
        self.logger = logging.getLogger("OLLAMA_CLIENT")
        self.host = self.config.ollama_host()
        self.model = self.config.ollama_model()

        # chat_id -> {"messages": [...], "last_activity": timestamp}
        self.conversations = {}

    def _cleanup_old_contexts(self):
        now = time.time()
        expired = [
            chat_id
            for chat_id, data in self.conversations.items()
            if now - data["last_activity"] > self.CONTEXT_TTL
        ]
        for chat_id in expired:
            del self.conversations[chat_id]


    async def stream_response(self, chat_id: int, user_message: str, callback):
        """
        Stream response from Ollama with context and call callback for each chunk.
        """
        try:
            self._cleanup_old_contexts()
            now = time.time()

            # Neue Conversation falls nötig
            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    "messages": [{"role": "system", "content": self.SYSTEM_CONTEXT}],
                    "last_activity": now,
                }

            conversation = self.conversations[chat_id]["messages"]

            # User Message anhängen
            conversation.append({"role": "user", "content": user_message})

            # Message Limit einhalten
            if len(conversation) > self.MAX_MESSAGES:
                conversation[:] = [conversation[0]] + conversation[-(self.MAX_MESSAGES - 1):]

            payload = {
                "model": self.model,
                "messages": conversation,
                "stream": True,
            }

            url = f"{self.host}/api/chat"

            full_response = ""
            buffer = ""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:

                    if resp.status != 200:
                        self.logger.error(f"Ollama API error: {resp.status}")
                        return "Fehler bei der Verbindung zum LLM."

                    async for chunk_bytes in resp.content.iter_chunked(1024):
                        buffer += chunk_bytes.decode("utf-8")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                import json
                                json_data = json.loads(line)

                                # Support für Ollama Streaming JSON
                                text = json_data.get("response") or json_data.get("message", {}).get("content")
                                done = json_data.get("done", False)

                                if text:
                                    full_response += text
                                    await callback(text)

                                if done:
                                    break

                            except Exception as e:
                                self.logger.debug(f"Chunk parsing failed: {e}")
                                continue

            # Assistant Antwort speichern im Kontext
            conversation.append({"role": "assistant", "content": full_response})
            self.conversations[chat_id]["last_activity"] = now

            return full_response

        except asyncio.TimeoutError:
            self.logger.error("Ollama streaming request timed out")
            return "Antwort zu lange, bitte erneut versuchen."
        except Exception as e:
            self.logger.error(f"Ollama streaming error: {e}")
            return "Fehler beim Streaming der Antwort."




    async def generate_response(self, chat_id: int, user_message: str) -> str:
        try:
            self._cleanup_old_contexts()
            now = time.time()

            # Neue Conversation falls nicht vorhanden
            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_CONTEXT}
                    ],
                    "last_activity": now,
                }

            conversation = self.conversations[chat_id]["messages"]

            # User Nachricht anhängen
            conversation.append({"role": "user", "content": user_message})

            # Message Limit einhalten
            if len(conversation) > self.MAX_MESSAGES:
                conversation[:] = (
                    [conversation[0]] + conversation[-(self.MAX_MESSAGES - 1):]
                )

            payload = {
                "model": self.model,
                "messages": conversation,
                "stream": False,
            }

            url = f"{self.host}/api/chat"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:

                    if response.status != 200:
                        self.logger.error(f"Ollama API error: {response.status}")
                        return "Fehler bei der Verbindung zum LLM."

                    result = await response.json()
                    assistant_reply = result["message"]["content"]

                    # Assistant Antwort speichern
                    conversation.append(
                        {"role": "assistant", "content": assistant_reply}
                    )

                    self.conversations[chat_id]["last_activity"] = now

                    return assistant_reply

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Fehler bei der Antwortgenerierung."
