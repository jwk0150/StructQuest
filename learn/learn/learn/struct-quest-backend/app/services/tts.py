"""
Edge TTS 语音合成服务
- 免费无需 API Key
- 支持中文多音色
- 返回 base64 编码音频（方便 WebSocket 传输）
"""

import edge_tts
import base64
from typing import Optional


class TTSService:
    """Edge TTS 语音合成服务"""

    # 预设音色列表（供用户选择）
    VOICES = {
        "xiaoxiao": {
            "id": "zh-CN-XiaoxiaoNeural",
            "name": "温柔女声",
            "desc": "温柔亲切，适合耐心讲解"
        },
        "yunxi": {
            "id": "zh-CN-YunxiNeural",
            "name": "阳光男声",
            "desc": "阳光开朗，充满活力"
        },
        "xiaoyi": {
            "id": "zh-CN-XiaoyiNeural",
            "name": "知性女声",
            "desc": "知性专业，适合学术讲解"
        },
        "yunyang": {
            "id": "zh-CN-YunyangNeural",
            "name": "沉稳男声",
            "desc": "沉稳厚重，适合严肃内容"
        },
        "xiaobei": {
            "id": "zh-CN-XiaobeiNeural",
            "name": "活泼女声",
            "desc": "活泼可爱，轻松愉快"
        },
        "xiaozhen": {
            "id": "zh-CN-XiaozhenNeural",
            "name": "亲和女声",
            "desc": "自然亲切，像朋友聊天"
        }
    }

    def __init__(self):
        pass

    def get_voice_id(self, voice_key: str) -> str:
        """获取语音 ID"""
        if voice_key in self.VOICES:
            return self.VOICES[voice_key]["id"]
        # 默认使用温柔女声
        return self.VOICES["xiaoxiao"]["id"]

    def list_voices(self) -> dict:
        """获取所有可用音色列表"""
        return self.VOICES

    async def synthesize(self, text: str, voice_key: str = "xiaoxiao") -> bytes:
        """
        合成语音，返回 MP3 二进制数据
        
        Args:
            text: 要合成的文本
            voice_key: 音色 key（如 'xiaoxiao', 'yunxi'）
            
        Returns:
            MP3 格式的音频二进制数据
        """
        voice = self.get_voice_id(voice_key)
        communicate = edge_tts.Communicate(text, voice)
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return audio_data

    async def synthesize_to_base64(
        self, 
        text: str, 
        voice_key: str = "xiaoxiao",
        max_length: int = 500
    ) -> Optional[str]:
        """
        合成语音并返回 base64 编码
        
        Args:
            text: 要合成的文本
            voice_key: 音色 key
            max_length: 最大文本长度（防止过长导致合成缓慢）
            
        Returns:
            base64 编码的 MP3 数据，失败返回 None
        """
        try:
            # 截断过长的文本
            if len(text) > max_length:
                text = text[:max_length] + "..."
                
            audio_bytes = await self.synthesize(text, voice_key)
            
            if not audio_bytes:
                return None
                
            return base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as e:
            print(f"[TTS] 合成失败: {e}")
            return None


# 全局单例
tts_service = TTSService()
