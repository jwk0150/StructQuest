"""
Agent 基类 — 多智能体系统核心基础设施

所有业务 Agent 继承此类，统一：
- LLM 调用（自动接入 LLMService / 同步兜底）
- JSON 响应解析与容错
- 决策日志记录（可观测性）
- RAG 检索集成
- 错误处理与降级策略

新增 Agent 步骤：
1. 继承 BaseAgent
2. 实现 name、description 属性
3. 实现 run() 方法（接收 state，返回更新的 state 字典）
4. 在 graph.py 中注册节点和边
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import time
import json
import re
import os

from app.agents.state import LearningState
from app.utils.logger import get_logger

logger = get_logger("base_agent")


class BaseAgent(ABC):
    """
    多智能体系统基类
    
    设计原则：
    - DRY：所有 Agent 共享的 LLM 调用/JSON 解析/日志 统一在此
    - 容错：LLM 不可用时自动降级到规则兜底
    - 可观测：每步决策都记录到 state.messages
    """

    # ── 子类必须实现的接口 ──

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent 名称（唯一标识）"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Agent 功能描述"""
        pass

    @abstractmethod
    def run(self, state: LearningState) -> Dict[str, Any]:
        """
        核心方法：执行 Agent 逻辑
        
        Args:
            state: 当前全局状态（只读取需要的字段）
        
        Returns:
            需要更新的状态字段字典（LangGraph 会自动 merge 到 state 中）
            
        注意：
        - 不要直接修改 state 参数！返回需要更新的字段即可
        - 只写入自己负责的字段，不要动其他 Agent 的产出
        """
        pass

    # ── 可选覆写的降级方法 ──

    def fallback(self, state: LearningState, error: Exception = None) -> Dict[str, Any]:
        """LLM 调用失败时的降级逻辑。子类建议覆写此方法提供有意义的默认值。"""
        self._log(state, f"使用默认降级策略: {error}", level="warn")
        return {}

    # ══════════════════════════════════════════════════
    #  日志系统
    # ══════════════════════════════════════════════════

    def _log(self, state: LearningState, message: str, level: str = "info") -> Dict[str, List]:
        """记录决策日志到 state.messages（用于前端展示决策过程）"""
        timestamp = time.strftime("%H:%M:%S")
        entry: Dict[str, Any] = {
            "timestamp": timestamp,
            "agent": self.name,
            "level": level,
            "message": message,
        }
        return {"messages": state.get("messages", []) + [entry]}

    # ══════════════════════════════════════════════════
    #  Prompt 模板工具
    # ══════════════════════════════════════════════════

    @staticmethod
    def _build_system_prompt(template: str, **kwargs) -> str:
        """填充 prompt 模板，自动检测缺失参数"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"[{__class__.__name__}] Prompt 模板缺少必要参数: {e}")

    # ══════════════════════════════════════════════════
    #  LLM 调用层（统一入口）
    # ══════════════════════════════════════════════════

    def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """
        同步调用 LLM —— 所有 Agent 的唯一调用入口
        
        优先级：
        1. 尝试使用已注入的 llm_provider (async wrapper)
        2. 回退到内置同步 OpenAI 调用
        
        Args:
            messages: 对话消息列表 [{"role": "...", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            LLM 响应文本
            
        Raises:
            RuntimeError: LLM 完全不可用时抛出
        """
        # 策略1: 使用外部注入的 provider
        if getattr(self, 'llm', None) is not None:
            import asyncio
            try:
                # 检查是否有正在运行的事件循环
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # 在运行中的事件循环内被同步调用（反模式，如直接在 async 路由中同步调用）
                # 降级到同步 fallback，避免新建线程池+独立事件循环导致的开销和连接泄漏
                logger.debug(
                    "[%s] 检测到运行中的事件循环，降级到同步 LLM 调用（建议用 asyncio.to_thread 包装）",
                    self.name,
                )
                return self._call_llm_fallback(messages, temperature=temperature, max_tokens=max_tokens)

            # 无运行中的事件循环（如 asyncio.to_thread 包装的独立线程）→ 安全地用 asyncio.run
            async def _async_call():
                return await self.llm.generate(messages, temperature=temperature, **kwargs)

            return asyncio.run(_async_call())

        # 策略2: 内置同步 OpenAI 兜底
        return self._call_llm_fallback(messages, temperature=temperature, max_tokens=max_tokens)

    def _call_llm_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """内置同步 OpenAI 调用（当外部 provider 不可用时使用）"""
        from dotenv import load_dotenv
        from pathlib import Path

        # ── 健壮的 .env 加载：在当前目录及多级父目录中查找 ──
        search_dir = Path.cwd()
        env_loaded = False
        for _ in range(6):  # 最多向上搜 5 级
            candidate = search_dir / ".env"
            if candidate.exists():
                load_dotenv(dotenv_path=str(candidate))
                env_loaded = True
                logger.debug("[%s] 加载 .env: %s", self.name, candidate)
                break
            search_dir = search_dir.parent
        if not env_loaded:
            # 回退到默认行为（搜索 cwd）
            load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")

        if not api_key:
            raise RuntimeError(
                f"[{self.name}] 未配置 OPENAI_API_KEY，无法调用 LLM。"
                f"请在 .env 文件中设置 OPENAI_API_KEY 和 OPENAI_BASE_URL。"
            )

        # 诊断日志：记录实际使用的配置（key 脱敏）
        masked_key = api_key[:8] + "***" if len(api_key) > 8 else "***"
        model = os.getenv("LLM_MODEL", "deepseek-chat")
        logger.info("[%s] 🔧 LLM fallback: base_url=%s, model=%s, key=%s, cwd=%s",
                   self.name, base_url or "(empty→api.openai.com!)", model, masked_key, Path.cwd())

        import openai
        import httpx
        # ★ trust_env=False 绕过 Windows 系统代理（国内直连 DeepSeek）
        http_client = httpx.Client(trust_env=False)
        client = openai.OpenAI(api_key=api_key, base_url=base_url, http_client=http_client)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as api_err:
            # 记录完整错误信息，方便排查
            err_str = str(api_err)
            logger.error("[%s] ❌ LLM API 调用失败: %s (type=%s)", self.name, err_str, type(api_err).__name__)
            raise

    # ══════════════════════════════════════════════════
    #  JSON 解析器（鲁棒提取）
    # ══════════════════════════════════════════════════

    @staticmethod
    def _sanitize_json_text(text: str) -> str:
        """
        清洗 LLM 返回文本中的中文标点和特殊字符，使 JSON 可解析。
        
        常见问题：
        - 大模型在 JSON 字符串值内使用中文引号 「」『』""'' 等
        - 中文破折号、省略号等非 ASCII 标点
        """
        import re
        
        # 常见的中文引号映射到标准英文引号
        CHINESE_QUOTE_MAP = {
            '\u201c': '"',   # "
            '\u201d': '"',   # "
            '\u2018': "'",   # '
            '\u2019': "'",   # '
            '\u300c': '"',   # 「
            '\u300d': '"',   # 」
            '\u300e': '"',   # 『
            '\u300f': '"',   # 』
            '\uff02': '"',   # ＂
            '\uff07': "'",   # ＇
            '\u00ab': '"',   # «
            '\u00bb': '"',   # »
            '\u2039': "'",   # ‹
            '\u203a': "'",   # ›
        }
        
        result = text
        for ch, replacement in CHINESE_QUOTE_MAP.items():
            result = result.replace(ch, replacement)
        
        result = result.replace('\u2014', '--')
        result = result.replace('\u2013', '-')
        result = result.replace('\u2026', '...')
        
        return result

    @staticmethod
    def _parse_json(text: str) -> Dict:
        """
        从 LLM 响应中可靠地提取 JSON 对象
        
        策略：
        1. 清洗中文标点后直接 json.loads
        2. 提取 ```json ... ``` 代码块后清洗再解析
        3. 正则匹配最外层 { ... } 后清洗再解析
        4. 如果仍失败，用 re 移除所有控制字符后重试
        """
        sanitize = BaseAgent._sanitize_json_text
        cleaned_text = sanitize(text).strip()
        
        # 策略1: 直接解析（清洗后）
        try:
            data = json.loads(cleaned_text)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, ValueError):
            pass

        # 策略2: ```json ... ``` （提取后清洗）
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_text)
        if match:
            try:
                inner = sanitize(match.group(1).strip())
                return json.loads(inner)
            except json.JSONDecodeError:
                pass

        # 策略3: 找最外层的 { ... }（清洗后）
        start = cleaned_text.find('{')
        end = cleaned_text.rfind('}')
        if start != -1 and end > start:
            try:
                json_str = cleaned_text[start:end + 1]
                json_str = sanitize(json_str)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 策略4: 终极清洗 — 移除所有 CJK 标点符号类 Unicode 字符
        try:
            import re as _re
            aggressive = _re.sub(r'[\u3000-\u303f\uff00-\uffef\u2010-\u2027\u2030-\u205e]', '', text)
            start = aggressive.find('{')
            end = aggressive.rfind('}')
            if start != -1 and end > start:
                return json.loads(aggressive[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

        raise ValueError(
            f"无法从 LLM 响应中提取有效 JSON。\n"
            f"原始响应前300字符:\n{text[:300]}"
        )

    # ══════════════════════════════════════════════════
    #  RAG 集成
    # ══════════════════════════════════════════════════

    def _retrieve_knowledge(
        self,
        query: str,
        top_k: int = 3,
        rag_service=None,
    ) -> str:
        """
        从知识库检索相关上下文
        
        Args:
            query: 检索查询
            top_k: 返回条数上限
            rag_service: 外部传入的 RAG 服务实例
            
        Returns:
            格式化的检索结果文本（空字符串表示无可用上下文）
        """
        if rag_service is None:
            # 尝试延迟导入
            try:
                from app.services.rag import rag_service as global_rag_service
                rag_service = global_rag_service
            except Exception:
                return ""

        try:
            context = rag_service.retrieve_context(query, k=top_k)
            # retrieve_context() 返回格式化字符串（非 dict），直接返回即可
            if not context or not context.strip():
                return ""
            return context
        except Exception as e:
            logger.warning("RAG 检索警告: %s", e)
            return ""

    # ══════════════════════════════════════════════════
    #  安全执行包装器
    # ══════════════════════════════════════════════════

    def safe_execute(
        self,
        state: LearningState,
        operation_name: str,
        fallback_data: Optional[Dict] = None,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        安全执行包装：自动捕获异常 + 降级 + 记录日志
        
        用法:
            success, result = self.safe_execute(state, "画像分析")
            if not success:
                # 使用 fallback 数据继续...
                
        Returns:
            (是否成功, 结果字典)
        """
        try:
            log_entry = self._log(state, f"开始执行: {operation_name}")
            return True, log_entry
        except Exception as e:
            error_log = self._log(
                state,
                f"{operation_name} 异常: {type(e).__name__}: {str(e)}",
                level="error",
            )
            fallback_result = self.fallback(state, error=e)
            return False, {
                **error_log,
                **(fallback_data or fallback_result),
            }

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"
