"""
D-ID 数字人视频生成服务

功能：
1. 调用 D-ID API 生成数字人说话视频
2. 视频本地缓存（按文本内容哈希），避免重复调用付费 API
3. 支持：自定义形象、多语言 TTS、口型完美同步

缓存策略：
- 输入相同文本 → 直接返回已缓存的视频路径（不调 API）
- 文本不同 → 生成新视频并保存到 static/videos/did/ 目录
- 缓存格式: did_{text_hash}_{voice_key}.mp4

使用前需要：
1. 注册 D-ID 账号 https://studio.d-id.com/
2. 获取 API Key（在 Account > API Keys）
3. 在 .env 中设置 DID_API_KEY
"""

import os
import json
import hashlib
import time
import asyncio
import httpx
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


class DIdService:
    """D-ID 数字人视频生成 + 缓存管理"""

    # D-API 端点（v1 版本）
    BASE_URL = "https://api.d-id.com"
    TALKS_URL = f"{BASE_URL}/talks"

    # 默认配置
    DEFAULT_CONFIG = {
        "driver_url": "expressions/driver-01.json",   # 表情驱动
        "config": {
            "fluent": True,
            "pad_audio": 0.5
        }
    }

    # ═══ 预设数字人形象 ═══
    # 使用 D-ID 新版 API 推荐的 image URL
    # 也可在 D-ID Studio (studio.d-id.com) 自定义形象后使用自己的图片 URL
    AVATARS = {
        # D-ID 官方推荐的新版 Presenter 图片 URL
        "emma": "https://d-id-public.s3.us-west-2.amazonaws.com/or-roman/origins/00.png",
        "james": "https://d-id-public.s3.us-west-2.amazonaws.com/or-clarence/origins/00.png",
        "amy": "https://d-id-public.s3.us-west-2.amazonaws.com/amelia/01/image.png",
        "alex": "https://d-id-public.s3.us-west-2.amazonaws.com/louie/01/image.png",

        # 教师角色（默认）
        "teacher_female": "https://d-id-public.s3.us-west-2.amazonaws.com/or-roman/origins/00.png",
        "teacher_male": "https://d-id-public.s3.us-west-2.amazonaws.com/or-clarence/origins/00.png",

        # 备选: 使用 d-id.com 域名下的图片
        "emma_alt": "https://api.d-id.com/images/romans.png",
        "james_alt": "https://api.d-id.com/images/clarence.png",
    }

    # 音色映射（D-ID voice_id）
    VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",
        "yunxi": "zh-CN-YunxiNeural",
        "xiaoyi": "zh-CN-XiaoyiNeural",
        "yunyang": "zh-CN-YunyangNeural",
        "xiaobei": "zh-CN-XiaobeiNeural",
        "xiaozhen": "zh-CN-XiaozhenNeural",
        # 英文备选
        "en_female": "en-US-JennyNeural",
        "en_male": "en-US-GuyNeural",
    }

    def __init__(self):
        self.api_key = os.getenv("DID_API_KEY", "")
        self.static_base = os.environ.get("STATIC_DIR", "/app/static")
        self.cache_dir = Path(self.static_base) / "videos" / "did"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # ★ 默认待机视频路径（预存一段视频，D-ID 额度耗尽时使用）
        self.default_video_path = self.cache_dir / "default_standby.mp4"

        # 初始化日志
        if self.api_key:
            masked_key = self.api_key[:6] + "..." + self.api_key[-4:] if len(self.api_key) > 10 else "***"
            print(f"[D-ID] [OK] 服务初始化完成 (Key: {masked_key})")
        else:
            print("[D-ID] [WARN] 未检测到 DID_API_KEY，数字人功能将不可用")

        # 检查默认视频
        if self.default_video_path.exists():
            size_kb = self.default_video_path.stat().st_size / 1024
            print(f"[D-ID] [VIDEO] 默认待机视频已就绪: {self.default_video_path.name} ({size_kb:.0f} KB)")
        else:
            print("[D-ID] [INFO] 未找到默认待机视频，将使用动画形象作为待机画面")

    @property
    def is_available(self) -> bool:
        """检查 API Key 是否配置"""
        return bool(self.api_key)

    @property
    def has_default_video(self) -> bool:
        """检查是否有预存的默认待机视频"""
        return self.default_video_path.exists() and self.default_video_path.stat().st_size > 0

    def get_default_video_url(self) -> str:
        """获取默认待机视频的 URL 路径"""
        if self.has_default_video:
            return f"/static/videos/did/{self.default_video_path.name}"
        return ""

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    # ════════════════════════════════
    #  缓存管理
    # ════════════════════════════════

    @staticmethod
    def text_hash(text: str) -> str:
        """生成文本的 SHA-256 哈希（用于缓存文件名）"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

    def get_cached_video_path(self, text: str, voice_key: str = "xiaoxiao") -> Optional[Path]:
        """
        检查是否有缓存的视频

        Returns:
            视频文件 Path，或 None（未缓存）
        """
        hash_val = self.text_hash(text)
        pattern = f"did_{hash_val}_{voice_key}.*"

        for ext in ["mp4", "webm"]:
            cached = self.cache_dir / f"did_{hash_val}_{voice_key}.{ext}"
            if cached.exists() and cached.stat().st_size > 0:
                file_size = cached.stat().st_size / 1024
                print(f"[D-ID] [OK] 命中缓存: {cached.name} ({file_size:.0f} KB)")
                return cached

        return None

    def save_to_cache(
        self,
        video_bytes: bytes,
        text: str,
        voice_key: str = "xiaoxiao",
        extension: str = "mp4"
    ) -> Path:
        """保存视频到缓存目录"""
        hash_val = self.text_hash(text)
        filename = f"did_{hash_val}_{voice_key}.{extension}"
        filepath = self.cache_dir / filename

        with open(filepath, 'wb') as f:
            f.write(video_bytes)

        file_size_kb = len(video_bytes) / 1024
        print(f"[D-ID] [SAVE] 已缓存: {filename} ({file_size_kb:.0f} KB)")

        return filepath

    # ════════════════════════════════
    #  D-ID API 调用
    # ════════════════════════════════

    async def generate_talk(
        self,
        text: str,
        voice_key: str = "xiaoxiao",
        avatar_key: str = "teacher_female",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        生成数字人说话视频（带缓存）

        Args:
            text: 要讲解的文本
            voice_key: 音色 key（如 xiaoxiao, yunxi）
            avatar_key: 形象 key（如 emma, james, teacher_female）
            use_cache: 是否启用缓存（默认开启）

        Returns:
            {
                "video_url": "/static/videos/did/xxx.mp4",  // 本地路径
                "is_cached": true/false,
                "duration": 12.5,
                "cost_credits": 0 (缓存时为0),
            }
        """

        if not self.api_key:
            raise ValueError("未配置 D-ID API Key。请在 .env 中添加 DID_API_KEY=your_key")

        # 截断过长文本（D-ID 单次限制约 500 字符）
        original_text = text
        if len(text) > 500:
            text = text[:497] + "..."

        # ===== 1️⃣ 先查缓存 =====
        if use_cache:
            cached_path = self.get_cached_video_path(text, voice_key)
            if cached_path:
                return {
                    "video_url": f"/static/videos/did/{cached_path.name}",
                    "is_cached": True,
                    "file_name": cached_path.name,
                    "message": "使用缓存视频"
                }

        # ===== 2️⃣ 无缓存 → 调用 D-ID API =====
        print(f"[D-ID] [START] 开始生成视频... (文本长度: {len(text)}, 形象: {avatar_key}, 音色: {voice_key})")

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:

                # ── Step A: 创建 talk 任务 ──
                print("[D-ID] Step 1/3: 提交任务...")

                image_url = self.AVATARS.get(avatar_key, self.AVATARS["teacher_female"])
                voice_id = self.VOICES.get(voice_key, self.VOICES["xiaoxiao"])

                # 构建请求 payload — 新版 D-API v1 格式 (image_url)
                # 注意: 旧版用 source_url，新版改用 image_url
                payload = {
                    "script": {
                        "type": "text",
                        "input": text,
                        "provider": {
                            "type": "microsoft",
                            "voice_id": voice_id,
                        },
                    },
                    "config": {
                        "fluent": True,
                        "pad_audio": 0.5,
                    }
                }

                # 使用 image_url 字段（新版 API）
                if image_url:
                    payload["image_url"] = image_url

                print(f"[D-ID]   形象URL: {image_url[:60]}...")
                print(f"[D-ID]   音色ID: {voice_id}")
                print(f"[D-ID]   Payload keys: {list(payload.keys())}")

                resp = await client.post(
                    self.TALKS_URL,
                    headers=self.headers,
                    json=payload
                )

                if resp.status_code != 201:
                    error_detail = resp.text[:500]
                    print(f"[D-ID] [ERR] 创建任务失败! HTTP {resp.status_code}")
                    print(f"[D-ID]   响应内容: {error_detail}")

                    # 更友好的错误提示
                    if resp.status_code == 401 or resp.status_code == 403:
                        raise Exception(
                            "D-API 认证失败(401/403)。请检查:\n"
                            "1. .env 中的 DID_API_KEY 是否正确\n"
                            "2. API Key 是否已过期或额度耗尽\n"
                            "3. 访问 https://studio.d-id.com/ 确认账号状态"
                        )
                    elif resp.status_code == 402:
                        raise Exception(
                            "D-ID 额度不足(402)。需要充值才能继续生成数字人视频。\n"
                            "访问 https://studio.d-id.com/account 查看套餐"
                        )
                    elif resp.status_code == 422:
                        raise Exception(
                            f"D-ID 参数错误(422): {error_detail}\n"
                            "可能原因: 音色ID不支持 或 形像URL无效"
                        )
                    else:
                        raise Exception(f"D-ID 创建任务失败 ({resp.status_code}): {error_detail}")

                task_data = resp.json()
                talk_id = task_data["id"]
                print(f"[D-ID]   [OK] 任务已创建: {talk_id}")

                # ── Step B: 轮询等待完成 ──
                print("[D-ID] Step 2/3: 等待渲染...")
                status_url = f"{self.TALKS_URL}/{talk_id}"
                max_wait = 180  # 最大等待 180 秒
                start_time = time.time()

                while True:
                    await asyncio.sleep(3)

                    elapsed = time.time() - start_time
                    if elapsed > max_wait:
                        raise TimeoutError(f"D-ID 渲染超时 ({max_wait}s)，任务可能仍在处理中")

                    try:
                        status_resp = await client.get(status_url, headers=self.headers)
                        status_data = status_resp.json()
                    except httpx.HTTPError as e:
                        print(f"[D-ID] [WARN] 轮询请求异常: {e}")
                        await asyncio.sleep(2)
                        continue

                    current_status = status_data.get("status", "")

                    if current_status == "done":
                        duration = elapsed
                        print(f"[D-ID] [OK] 渲染完成! ({duration:.1f}s)")

                        video_url = status_data.get("result_url")
                        if not video_url:
                            print(f"[D-ID] [WARN] 无 result_url，完整响应: {json.dumps(status_data)[:300]}")
                            raise Exception("D-ID 返回成功但无视频链接")

                        # 下载视频到本地
                        print("[D-ID] Step 3/3: 下载视频...")
                        try:
                            video_resp = await client.get(video_url)
                            video_bytes = video_resp.content

                            if len(video_bytes) < 1000:
                                print(f"[D-ID] [WARN] 视频文件过小 ({len(video_bytes)} bytes)，可能下载失败")
                                raise Exception("视频文件异常，可能是临时错误")

                            saved_path = self.save_to_cache(video_bytes, text, voice_key)

                            return {
                                "video_url": f"/static/videos/did/{saved_path.name}",
                                "is_cached": False,
                                "file_name": saved_path.name,
                                "duration": status_data.get("duration", 0),
                                "talk_id": talk_id,
                                "message": f"视频生成完成并已缓存 ({duration:.1f}s)"
                            }
                        except httpx.HTTPError as download_err:
                            print(f"[D-ID] [ERR] 下载视频失败: {download_err}")
                            raise Exception(f"无法下载生成的视频: {download_err}")

                    elif current_status == "error":
                        error_info = status_data.get("error", {})
                        error_msg = json.dumps(error_info) if isinstance(error_info, dict) else str(error_info)
                        print(f"[D-ID] [ERR] 任务出错: {error_msg}")
                        raise Exception(f"D-ID 渲染错误: {error_msg}")

                    elif current_status in ["created", "processing"]:
                        progress = status_data.get("progress", 0)
                        if int(elapsed) % 10 < 3:  # 每10秒打印一次，避免刷屏
                            print(f"[D-ID] [WAIT] 进度 {progress}% ({elapsed:.0f}s/{max_wait}s)")
                    else:
                        print(f"[D-ID] [INFO] 状态: {current_status}")
                        await asyncio.sleep(3)

        except httpx.TimeoutException as e:
            print(f"[D-ID] [ERR] 请求超时: {e}")
            raise TimeoutError(f"D-ID API 请求超时: {e}")
        except ValueError as e:
            # JSON 解析等错误
            print(f"[D-ID] [ERR] 数据解析错误: {e}")
            traceback.print_exc()
            raise Exception(f"D-ID 返回数据格式异常: {e}")
        except Exception as e:
            print(f"[D-ID] [ERR] 未知错误: {type(e).__name__}: {e}")
            traceback.print_exc()
            raise

    async def list_avatars(self) -> Dict[str, Dict[str, str]]:
        """返回可用数字人形象列表"""
        result = {}
        for key, url in self.AVATARS.items():
            result[key] = {"name": key.replace("_", " ").title(), "url": url}
        return result

    async def check_quota(self) -> Dict[str, Any]:
        """查询 D-ID 剩余额度"""
        if not self.is_available:
            return {"available": False, "reason": "未配置 API Key"}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{self.BASE_URL}/user", headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    remaining = data.get("remaining_credits", 0)
                    used = data.get("total_used", 0)
                    print(f"[D-ID] [STATS] 额度信息: 剩余={remaining}, 已用={used}")
                    return {
                        "available": True,
                        "remaining_credits": remaining,
                        "total_used": used
                    }
                else:
                    print(f"[D-ID] [WARN] 查询额度失败: HTTP {resp.status_code}")
        except httpx.TimeoutException:
            print("[D-ID] [WARN] 查询额度超时")
        except Exception as e:
            print(f"[D-ID] [WARN] 查询额度异常: {e}")

        return {"available": True, "remaining_credits": "unknown"}


# 全局单例
did_service = DIdService()