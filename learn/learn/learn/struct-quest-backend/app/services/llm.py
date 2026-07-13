"""
AI LLM Service: multi-provider, auto-failover, HTTP status code parsing
"""
import abc, json, os, traceback, re
from typing import Any, AsyncGenerator, Optional, List, Dict, Tuple
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

ERROR_MAP = {
    401: "API Key invalid or unauthorized. Check LLM_API_KEY.",
    402: "Account balance insufficient. Top up or switch provider.",
    403: "No model access permission. Check LLM_MODEL.",
    404: "API endpoint error. Check LLM_BASE_URL.",
    429: "Too many requests. Please retry later.",
    500: "AI server error. Please retry later.",
    502: "AI server gateway error. Please retry later.",
    503: "AI server temporarily unavailable. Please retry later.",
}

class LLMProvider(abc.ABC):
    name: str = "unknown"
    @abc.abstractmethod
    async def generate_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        pass
    async def check_health(self) -> Tuple[bool, str]:
        return True, ""

class OpenAIProvider(LLMProvider):
    name = "openai"
    def __init__(self, api_key: str, model: str, base_url: str, label: str = ""):
        import httpx
        # ★ trust_env=False 绕过 Windows 系统代理，直连 API
        http_client = httpx.AsyncClient(trust_env=False)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=http_client)
        self.model = model
        self.base_url = base_url
        self.label = label or base_url

    async def generate_stream(self, messages: List[Dict[str, str]], system_prompt: str = None) -> AsyncGenerator[str, None]:
        valid_messages = [m for m in messages if m.get("content")]
        if system_prompt:
            # 在自定义提示前始终保留基础身份指令
            combined = "You are a professional Data Structures AI assistant named StructQuest AI. Answer in Chinese.\n\n" + system_prompt
            valid_messages.insert(0, {"role": "system", "content": combined})
        elif not any(m.get("role") == "system" for m in valid_messages):
            valid_messages.insert(0, {
                "role": "system",
                "content": "You are a professional Data Structures AI assistant named StructQuest AI. Answer in Chinese."
            })
        print(f"\n[LLM] Call: {self.label} | Model: {self.model} | URL: {self.base_url} | Messages: {len(valid_messages)}")
        try:
            stream = await self.client.chat.completions.create(
                model=self.model, messages=valid_messages, stream=True, timeout=60,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_info = self._parse_error(e)
            print(f"[LLM] ERROR: {json.dumps(error_info, ensure_ascii=False)}")
            raise LLMError(**error_info)

    def _parse_error(self, e: Exception) -> dict:
        err_str = str(e)
        status_code = 0
        if hasattr(e, 'status_code'): status_code = e.status_code
        body = getattr(e, 'body', '') or getattr(e, 'message', '')
        match = re.search(r'(\d{3})', err_str)
        if match and not status_code:
            status_code = int(match.group(1))
        msg = ERROR_MAP.get(status_code, f"AI call failed: {err_str[:200]}")
        return {"status_code": status_code, "message": msg, "detail": err_str[:300], "provider": self.label, "model": self.model}

    async def check_health(self) -> Tuple[bool, str]:
        try:
            await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "ping"}], max_tokens=1, timeout=10,
            )
            return True, "ok"
        except Exception as e:
            return False, self._parse_error(e)["message"]

class AnthropicProvider(LLMProvider):
    name = "anthropic"
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    async def generate_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(max_tokens=4096, messages=messages, model=self.model) as stream:
            async for text in stream.text_stream: yield text
    async def check_health(self) -> Tuple[bool, str]:
        return True, "ok"

class LLMError(Exception):
    def __init__(self, status_code=0, message="", detail="", provider="", model=""):
        self.status_code = status_code; self.message = message; self.detail = detail
        self.provider = provider; self.model = model
        super().__init__(message)

class LLMService:
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        from dotenv import load_dotenv
        load_dotenv()

        # Primary: SiliconFlow
        main_key = os.getenv("LLM_API_KEY")
        main_base = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        main_model = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        if main_key:
            self.providers["primary"] = OpenAIProvider(
                api_key=main_key, model=main_model, base_url=main_base, label="Primary(SiliconFlow)")
            print(f"[LLM] Primary registered: {main_base} / {main_model}")

        # Fallback: DeepSeek
        fallback_key = os.getenv("FALLBACK_API_KEY") or os.getenv("OPENAI_API_KEY")
        fallback_base = os.getenv("FALLBACK_BASE_URL") or os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        fallback_model = os.getenv("FALLBACK_MODEL", "deepseek-chat")
        if fallback_key:
            self.providers["fallback"] = OpenAIProvider(
                api_key=fallback_key, model=fallback_model, base_url=fallback_base, label="Fallback(DeepSeek)")
            print(f"[LLM] Fallback registered: {fallback_base} / {fallback_model}")

        # Legacy: OPENAI_API_KEY
        openai_key = os.getenv("OPENAI_API_KEY")
        openai_base = os.getenv("OPENAI_BASE_URL")
        if openai_key and "openai" not in self.providers:
            self.providers["openai"] = OpenAIProvider(api_key=openai_key, base_url=openai_base, model="deepseek-chat", label="Legacy(OpenAI)")

        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers["anthropic"] = AnthropicProvider(anthropic_key)
            print("[LLM] Anthropic registered")

        if not self.providers:
            print("[LLM] No AI providers available! Set LLM_API_KEY in .env")

    def get_provider(self, preferred: str = None) -> Optional[LLMProvider]:
        if preferred and preferred in self.providers:
            return self.providers[preferred]
        for p in ["primary", "fallback", "openai", "anthropic"]:
            if p in self.providers:
                return self.providers[p]
        return None

    async def chat_with_failover(self, messages: List[Dict[str, str]], system_prompt: str = None) -> AsyncGenerator[dict, None]:
        """Stream with auto-failover. Yields {type: chunk|failover|error, ...}
        
        Args:
            messages: 对话消息列表
            system_prompt: 可选的自定义系统提示（如每日学习任务 Prompt）
        """
        used = set()
        for _ in range(len(self.providers)):
            provider = self.get_provider()
            if not provider:
                yield {"type": "error", "status_code": 0, "message": "All AI services unavailable."}
                return
            pname = [k for k, v in self.providers.items() if v is provider][0]
            if pname in used: continue
            used.add(pname)
            try:
                async for chunk in provider.generate_stream(messages, system_prompt=system_prompt):
                    yield {"type": "chunk", "content": chunk}
                return
            except LLMError as e:
                print(f"[LLM] Provider '{pname}' failed: HTTP {e.status_code} - {e.message}")
                if len(used) < len(self.providers):
                    yield {"type": "failover", "from": pname, "reason": e.message, "status_code": e.status_code}
                else:
                    yield {"type": "error", "status_code": e.status_code, "message": e.message, "detail": e.detail}
            except Exception as e:
                print(f"[LLM] Provider '{pname}' unknown error: {traceback.format_exc()}")
                if len(used) < len(self.providers):
                    yield {"type": "failover", "from": pname, "reason": str(e)[:100]}
                else:
                    yield {"type": "error", "status_code": 0, "message": f"AI error: {str(e)[:100]}"}

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        非流式 LLM 调用 —— 收集 chat_with_failover 的全部 chunk 后返回完整结果。

        用于 PPT 大纲生成等需要完整 JSON 响应的场景。

        Returns:
            {"content": str, "provider": str, "model": str}
        失败时抛出异常。
        """
        full_content = []
        provider_used = None
        error_detail = None

        async for event in self.chat_with_failover(messages):
            if event["type"] == "chunk":
                full_content.append(event.get("content", ""))
            elif event["type"] == "failover":
                # 故障切换：丢弃之前的内容，重新收集
                full_content = []
                provider_used = event.get("from", "")
            elif event["type"] == "error":
                error_detail = event.get("message", "Unknown error")
                break

        if error_detail and not full_content:
            raise Exception(f"LLM调用失败: {error_detail}")

        return {
            "content": "".join(full_content),
            "provider": provider_used or "unknown",
        }

    async def check_all_health(self) -> List[dict]:
        results = []
        for name, provider in self.providers.items():
            ok, msg = await provider.check_health()
            results.append({
                "name": name, "label": getattr(provider, 'label', name),
                "model": getattr(provider, 'model', ''), "ok": ok, "message": msg,
            })
        return results

llm_service = LLMService()
