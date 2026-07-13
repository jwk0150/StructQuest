"""
讯飞虚拟人交互平台 服务

基于讯飞虚拟人 WebSocket API，将文本转为数字人说话视频（含音频）。
支持：自定义形象、多种音色、视频本地缓存

API 文档：https://www.yuque.com/xnrpt/bbc1du/xamwb751mbpgeg2o

鉴权方式：hmac-sha256 签名（与讯飞开放平台合成接口一致）

使用流程：
1. 在 https://virtual-man.xfyun.cn 创建应用
2. 获取 APPID、APIKey、APISecret、接口服务ID(SceneId)
3. 在 .env 中配置 IFYTEK_VH_* 系列变量
"""

import os
import json
import hashlib
import hmac
import base64
import time
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote

import websockets
import httpx


class IflytekVirtualHumanService:
    """讯飞虚拟人交互平台 —— 文本 -> 数字人视频（含语音）"""

    # API 端点
    HOST = "avatar.cn-huadong-1.xf-yun.com"
    PATH = "/v1/interact"
    WS_URL = f"wss://{HOST}{PATH}"

    # 音色映射（讯飞发音人）
    VOICES = {
        "xiaoxiao": {"vcn": "x4_lingxiaoxuan_oral", "name": "晓晓（温柔女声）"},
        "xiaoyi":   {"vcn": "x4_lingxiaoyi_oral",   "name": "晓伊（知性女声）"},
        "xiaobei":  {"vcn": "x4_lingxiaobei_oral",  "name": "晓北（活泼女声）"},
        "xiaozhen": {"vcn": "x4_lingxiaozhen_oral", "name": "晓真（亲和女声）"},
        "yunxi":    {"vcn": "x4_lingyunxi_oral",    "name": "云希（阳光男声）"},
        "yunyang":  {"vcn": "x4_lingyunyang_oral",  "name": "云扬（沉稳男声）"},
        "default_female": {"vcn": "x4_lingxiaoxuan_oral", "name": "默认女声"},
        "default_male":   {"vcn": "x4_lingyunxi_oral",    "name": "默认男声"},
    }

    # 默认参数
    DEFAULT_AVATAR_ID = ""
    DEFAULT_PROTOCOL = "xrtc"
    DEFAULT_FPS = 25
    DEFAULT_BITRATE = 2000
    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1920

    def __init__(self):
        self.app_id = os.getenv("IFYTEK_VH_APP_ID", "")
        self.api_key = os.getenv("IFYTEK_VH_API_KEY", "")
        self.api_secret = os.getenv("IFYTEK_VH_API_SECRET", "")
        self.scene_id = os.getenv("IFYTEK_VH_SCENE_ID", "")

        self.avatar_id = os.getenv("IFYTEK_VH_AVATAR_ID", self.DEFAULT_AVATAR_ID)
        self.default_vcn = os.getenv("IFYTEK_VH_DEFAULT_VCN", "x4_lingxiaoxuan_oral")

        self.static_base = os.environ.get("STATIC_DIR", "/app/static")
        self.cache_dir = Path(self.static_base) / "videos" / "iflytek"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.connect_timeout = float(os.getenv("IFYTEK_VH_CONNECT_TIMEOUT", "15"))
        self.render_timeout = float(os.getenv("IFYTEK_VH_RENDER_TIMEOUT", "120"))

        if self.is_available:
            print(f"[iFlytek-VH] [OK] 服务初始化完成")
            print(f"[iFlytek-VH]    APP_ID: {self.app_id[:6]}...")
            print(f"[iFlytek-VH]    Scene: {self.scene_id}")
            print(f"[iFlytek-VH]    Avatar: {self.avatar_id or '(使用场景默认)'}")
        else:
            missing = []
            if not self.app_id: missing.append("IFYTEK_VH_APP_ID")
            if not self.api_key: missing.append("IFYTEK_VH_API_KEY")
            if not self.api_secret: missing.append("IFYTEK_VH_API_SECRET")
            if not self.scene_id: missing.append("IFYTEK_VH_SCENE_ID")
            print(f"[iFlytek-VH] [WARN] 未完整配置，缺少: {', '.join(missing)}")

    @property
    def is_available(self) -> bool:
        return bool(self.app_id and self.api_key and self.api_secret and self.scene_id)

    # ================================================================
    #  鉴权：hmac-sha256 签名
    # ================================================================

    @staticmethod
    def _rfc1123_time() -> str:
        """生成 RFC 1123 格式时间（GMT 时区）"""
        tz = timezone(timedelta(hours=0))
        now = datetime.now(tz)
        return now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def _build_auth_url(self) -> str:
        """
        构建带鉴权参数的完整 WebSocket URL
        签名步骤：
        1. 待签名字符串: host + date + request-line
        2. hmac-sha256 签名 -> base64
        3. 组装 authorization 参数 -> base64
        4. 拼接到 URL
        """
        date_str = self._rfc1123_time()
        host = self.HOST
        path = self.PATH

        signature_origin = (
            f"host: {host}\n"
            f"date: {date_str}\n"
            f"GET {path} HTTP/1.1"
        )

        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode("utf-8"),
                signature_origin.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        authorization_raw = (
            f'api_key="{self.api_key}",'
            f'algorithm="hmac-sha256",'
            f'headers="host date request-line",'
            f'signature="{signature}"'
        )
        authorization = base64.b64encode(
            authorization_raw.encode("utf-8")
        ).decode("utf-8")

        query_params = urlencode({
            "authorization": authorization,
            "host": host,
            "date": date_str,
        }, quote_via=quote)

        return f"{self.WS_URL}?{query_params}"

    # ================================================================
    #  缓存管理
    # ================================================================

    @staticmethod
    def text_hash(text: str) -> str:
        """文本 SHA-256 哈希（16 位，用于缓存文件名）"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def get_cached_path(self, text: str, voice_key: str = "xiaoxiao") -> Optional[Path]:
        """检查缓存"""
        h = self.text_hash(text)
        for ext in ["mp4", "webm", "mp3"]:
            p = self.cache_dir / f"iflytek_{h}_{voice_key}.{ext}"
            if p.exists() and p.stat().st_size > 1000:
                print(f"[iFlytek-VH] [CACHE] 命中: {p.name} ({p.stat().st_size / 1024:.0f} KB)")
                return p
        return None

    def save_to_cache(self, data: bytes, text: str, voice_key: str, ext: str = "mp4") -> Path:
        """保存到缓存"""
        h = self.text_hash(text)
        p = self.cache_dir / f"iflytek_{h}_{voice_key}.{ext}"
        p.write_bytes(data)
        print(f"[iFlytek-VH] [SAVE] 已缓存: {p.name} ({len(data) / 1024:.0f} KB)")
        return p

    # ================================================================
    #  核心：文本 -> 数字人视频
    # ================================================================

    async def generate(
        self,
        text: str,
        voice_key: str = "xiaoxiao",
        avatar_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        将文本转为数字人说话视频（实时流式）

        讯飞 API 返回的是 xrtc 实时流，非 MP4 文件。
        通过 WebSocket 接收 stream_url，前端可直接播放。

        Returns:
            {"stream_url": "xrtcs://...", "user_sign": "...", "appid": "...",
             "is_cached": False, "message": "..."}
        """
        if not self.is_available:
            raise ValueError("讯飞虚拟人未配置。请在 .env 中设置 IFYTEK_VH_* 系列变量")

        if len(text) > 500:
            text = text[:497] + "..."

        # 缓存（缓存 stream URL 无意义，但缓存 text hash 避免重复请求）
        cache_key = self.text_hash(text) + "_" + voice_key

        # -- 1. 生成鉴权 URL --
        ws_url = self._build_auth_url()
        print(f"[iFlytek-VH] [CONNECT] 连接 WebSocket...")

        # -- 2. WebSocket 交互 --
        voice_cfg = self.VOICES.get(voice_key, self.VOICES["xiaoxiao"])
        vcn = voice_cfg["vcn"]
        avatar = avatar_id or self.avatar_id

        request_id = uuid.uuid4().hex
        stream_url = None
        user_sign = None
        stream_appid = None
        cid = None

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"Content-Type": "application/json"},
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=16 * 1024 * 1024,
            ) as ws:
                print(f"[iFlytek-VH] [OK] WebSocket 已连接")

                # -- 发送 start 命令（TTS text 放在参数中）--
                start_msg = {
                    "header": {
                        "app_id": self.app_id,
                        "request_id": request_id,
                        "ctrl": "start",
                        "scene_id": self.scene_id,
                    },
                    "parameter": {
                        "avatar": {
                            "stream": {
                                "protocol": self.DEFAULT_PROTOCOL,
                                "fps": self.DEFAULT_FPS,
                                "bitrate": self.DEFAULT_BITRATE,
                                "alpha": 0,
                            },
                            "width": self.DEFAULT_WIDTH,
                            "height": self.DEFAULT_HEIGHT,
                        },
                        "tts": {
                            "vcn": vcn,
                            "speed": 50,
                            "pitch": 50,
                            "volume": 50,
                            "text": base64.b64encode(
                                text.encode("utf-8")
                            ).decode("ascii"),
                        },
                    },
                }
                if avatar:
                    start_msg["parameter"]["avatar"]["avatar_id"] = avatar

                await ws.send(json.dumps(start_msg, ensure_ascii=False))
                print(f"[iFlytek-VH] [SEND] 已发送 start (含TTS文本, {len(text)}字)")

                # -- 接收流信息 --
                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    except asyncio.TimeoutError:
                        break

                    if isinstance(raw, str):
                        try:
                            msg = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        header = msg.get("header", {})
                        code = header.get("code", 0)
                        if code != 0:
                            err_msg = header.get("message", "未知错误")
                            print(f"[iFlytek-VH] [ERR] code={code}: {err_msg}")
                            raise Exception(f"讯飞虚拟人返回错误 (code={code}): {err_msg}")

                        payload = msg.get("payload", {})
                        avatar_data = payload.get("avatar", {})

                        event_type = avatar_data.get("event_type", "")
                        print(f"[iFlytek-VH] [RECV] event={event_type}")

                        if event_type == "stream_info":
                            stream_url = avatar_data.get("stream_url", "")
                            stream_ext = avatar_data.get("stream_extend", {})
                            user_sign = stream_ext.get("user_sign", "")
                            stream_appid = stream_ext.get("appid", "")
                            print(f"[iFlytek-VH] [STREAM] URL获取成功")

                        elif event_type == "stream_start":
                            cid = avatar_data.get("cid", "")
                            print(f"[iFlytek-VH] [START] 流已开始 cid={cid}")
                            break  # 流已启动，可以返回了

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"[iFlytek-VH] [ERR] WebSocket异常关闭: {e}")
            if not stream_url:
                raise Exception(f"讯飞虚拟人连接异常关闭: {e}")

        if not stream_url:
            raise Exception("讯飞虚拟人未返回流地址")

        return {
            "stream_url": stream_url,
            "user_sign": user_sign,
            "appid": stream_appid,
            "cid": cid,
            "is_cached": False,
            "message": f"实时流已就绪 ({len(text)}字)",
        }

    # ================================================================
    #  辅助方法
    # ================================================================

    def get_voice_id(self, voice_key: str) -> str:
        return self.VOICES.get(voice_key, self.VOICES["xiaoxiao"])["vcn"]

    def list_voices(self) -> Dict[str, Dict[str, str]]:
        return {
            k: {"vcn": v["vcn"], "name": v["name"]}
            for k, v in self.VOICES.items()
        }

    async def check_quota(self) -> Dict[str, Any]:
        return {
            "available": self.is_available,
            "app_id": self.app_id[:6] + "..." if self.app_id else None,
            "scene_id": self.scene_id,
        }


# 全局单例
iflytek_vh_service = IflytekVirtualHumanService()
