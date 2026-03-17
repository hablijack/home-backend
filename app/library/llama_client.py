import asyncio
import aiohttp
import logging
import time
from library.Configuration import Configuration
from library.tools import AVAILABLE_TOOLS, get_tool_schemas
from library.prompt_firewall import PromptFirewall


class LlamaClient:
    CONTEXT_TTL = 180
    MAX_MESSAGES = 10

    SYSTEM_CONTEXT = (
        "Du bist ein hilfreicher Assistent der Nutzern Chats antwortet. "
        "Antworte immer auf deutsch und verwende keine Textformatierung außer Zeilenumbrüchen. "
        "Antworte in maximal 600 Wörtern. "
        "WICHTIG: Wenn du dir bei Fakten unsicher bist, aktuelle Informationen brauchst oder etwas nachschlagen musst, "
        "verwende IMMER das search_web Tool. Erfinde keine Antworten - suche lieber nach der Information!"
    )

    def __init__(self):
        self.config = Configuration()
        self.logger = logging.getLogger("LLAMA_CLIENT")
        self.host = self.config.llama_host_gemma()
        self.model = self.config.llama_model_gemma()
        self.tools = get_tool_schemas()
        self.firewall = PromptFirewall(self.config)

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
        try:
            self._cleanup_old_contexts()
            now = time.time()

            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    "messages": [{"role": "system", "content": self.SYSTEM_CONTEXT}],
                    "last_activity": now,
                }

            conversation = self.conversations[chat_id]["messages"]

            conversation.append({"role": "user", "content": user_message})

            if len(conversation) > self.MAX_MESSAGES:
                conversation[:] = [conversation[0]] + conversation[
                    -(self.MAX_MESSAGES - 1) :
                ]

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
                        self.logger.error(f"Llama API error: {resp.status}")
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

                                text = json_data.get("response") or json_data.get(
                                    "message", {}
                                ).get("content")
                                done = json_data.get("done", False)

                                if text:
                                    full_response += text
                                    await callback(text)

                                if done:
                                    break

                            except Exception as e:
                                self.logger.debug(f"Chunk parsing failed: {e}")
                                continue

            conversation.append({"role": "assistant", "content": full_response})
            self.conversations[chat_id]["last_activity"] = now

            return full_response

        except asyncio.TimeoutError:
            self.logger.error("Llama streaming request timed out")
            return "Antwort zu lange, bitte erneut versuchen."
        except Exception as e:
            self.logger.error(f"Llama streaming error: {e}")
            return "Fehler beim Streaming der Antwort."

    async def generate_response(self, chat_id: int, user_message: str) -> str:
        try:
            self._cleanup_old_contexts()
            now = time.time()

            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    "messages": [{"role": "system", "content": self.SYSTEM_CONTEXT}],
                    "last_activity": now,
                }

            conversation = self.conversations[chat_id]["messages"]

            conversation.append({"role": "user", "content": user_message})

            if len(conversation) > self.MAX_MESSAGES:
                conversation[:] = [conversation[0]] + conversation[
                    -(self.MAX_MESSAGES - 1) :
                ]

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
                        self.logger.error(f"Llama API error: {response.status}")
                        return "Fehler bei der Verbindung zum LLM."

                    result = await response.json()
                    if "message" in result:
                        assistant_reply = result["message"]["content"]
                    elif "choices" in result and len(result["choices"]) > 0:
                        assistant_reply = result["choices"][0]["message"]["content"]
                    else:
                        self.logger.error(f"Unexpected response format: {result}")
                        return "Unerwartete Antwort vom LLM."

                    conversation.append(
                        {"role": "assistant", "content": assistant_reply}
                    )

                    self.conversations[chat_id]["last_activity"] = now

                    return assistant_reply

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "Fehler bei der Antwortgenerierung."

    async def chat_with_tools(self, chat_id: int, user_message: str) -> str:
        try:
            firewall_result = await self.firewall.check(user_message)
            if not firewall_result.allowed:
                self.logger.warning(
                    f"Blocked prompt from chat {chat_id}: "
                    f"category={firewall_result.category}, "
                    f"similarity={firewall_result.similarity:.3f}"
                )
                return self.firewall.block_message

            self._cleanup_old_contexts()
            now = time.time()

            if chat_id not in self.conversations:
                self.conversations[chat_id] = {
                    "messages": [{"role": "system", "content": self.SYSTEM_CONTEXT}],
                    "last_activity": now,
                }

            conversation = self.conversations[chat_id]["messages"]
            conversation.append({"role": "user", "content": user_message})

            if len(conversation) > self.MAX_MESSAGES:
                conversation[:] = [conversation[0]] + conversation[
                    -(self.MAX_MESSAGES - 1) :
                ]

            payload = {
                "model": self.model,
                "messages": conversation,
                "tools": self.tools,
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
                        self.logger.error(f"Llama API error: {response.status}")
                        return "Fehler bei der Verbindung zum LLM."

                    result = await response.json()
                    self.logger.debug(f"Llama response: {result}")

                    if "message" in result:
                        assistant_message = result["message"]
                    elif "choices" in result and len(result["choices"]) > 0:
                        assistant_message = result["choices"][0]["message"]
                    else:
                        self.logger.error(f"Unexpected response format: {result}")
                        return "Unerwartete Antwortformat vom LLM."

                    tool_calls = assistant_message.get("tool_calls", [])

                    if tool_calls:
                        self.logger.info(
                            f"Tool calls detected: {[tc.get('function', {}).get('name') for tc in tool_calls]}"
                        )

                        conversation.append(
                            {
                                "role": "assistant",
                                "content": assistant_message.get("content"),
                                "tool_calls": tool_calls,
                            }
                        )

                        for tool_call in tool_calls:
                            func_name = tool_call.get("function", {}).get("name")
                            func_args = tool_call.get("function", {}).get(
                                "arguments", {}
                            )

                            if isinstance(func_args, str):
                                import json

                                func_args = json.loads(func_args)

                            func = AVAILABLE_TOOLS.get(func_name)
                            if func:
                                try:
                                    if asyncio.iscoroutinefunction(func):
                                        func_result = await func(**func_args)
                                    else:
                                        func_result = func(**func_args)

                                    conversation.append(
                                        {
                                            "role": "tool",
                                            "tool_call_id": tool_call.get("id"),
                                            "content": str(func_result),
                                        }
                                    )
                                    self.logger.info(
                                        f"Tool {func_name} result: {func_result}"
                                    )
                                except Exception as e:
                                    self.logger.error(f"Tool {func_name} error: {e}")
                                    conversation.append(
                                        {
                                            "role": "tool",
                                            "tool_call_id": tool_call.get("id"),
                                            "content": f"Fehler: {e}",
                                        }
                                    )
                            else:
                                self.logger.warning(f"Unknown tool: {func_name}")

                        payload["messages"] = conversation

                        async with session.post(
                            url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=300),
                        ) as final_response:
                            if final_response.status != 200:
                                return "Fehler bei der Verbindung zum LLM."

                            final_result = await final_response.json()
                            if "message" in final_result:
                                assistant_reply = final_result["message"]["content"]
                            elif (
                                "choices" in final_result
                                and len(final_result["choices"]) > 0
                            ):
                                assistant_reply = final_result["choices"][0]["message"][
                                    "content"
                                ]
                            else:
                                self.logger.error(
                                    f"Unexpected final response format: {final_result}"
                                )
                                return "Unerwartete Antwort vom LLM."
                            conversation.append(
                                {"role": "assistant", "content": assistant_reply}
                            )
                    else:
                        assistant_reply = assistant_message.get("content", "")
                        conversation.append(
                            {"role": "assistant", "content": assistant_reply}
                        )

                    self.conversations[chat_id]["last_activity"] = now
                    return assistant_reply

        except Exception as e:
            self.logger.error(f"Error in chat_with_tools: {e}")
            return "Fehler bei der Antwortgenerierung."

    async def health_check(self):
        try:
            url = f"{self.host}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
