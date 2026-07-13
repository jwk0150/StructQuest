# 数字人老师功能 - 实现说明

## 功能概览

已实现完整的**数字人老师在线讲解系统**，包含：
- ✅ Live2D 数字人形象（左侧展示）
- ✅ AI 对话交互（右侧聊天区）
- ✅ TTS 语音合成（Edge TTS，免费）
- ✅ 语音播放 + 口型同步动画
- ✅ 多音色切换（6 种中文音色）
- ✅ 实时流式输出（WebSocket）

---

## 界面布局

```
┌─────────────────────────────────────┐
│ 🧑🏫 数字人老师    已连接 🟢  [🎙️][⚙️] │  ← 头部（含音色选择）
├──────────┬──────────────────────────┤
│          │                          │
│  ┌────┐  │   🤖 你好！我是你的AI     │
│  │Live│  │      数字人老师...       │
│  │2D  │  │                          │
│  │老师│  │   👤 解释一下链表         │
│  │形象│  │                          │
│  │ ~~~│  │   🤖 链表是一种线性数据... │
│  └────┘  │     ▓▓▓▓▓░ (打字中)      │
│ 🔊●●○○ │  │                         │
├──────────┴──────────────────────────┤
│ ▓▓▓▓▓▓▓▓▓░░░░  [⏹停止]           │  ← 语音控制条
│ [解释一下] [举个例子] [通俗地说]      │  ← 快捷标签
│ [输入问题...]              [发送]   │  ← 输入框
└─────────────────────────────────────┘
```

---

## 新增/修改的文件

### 后端（Python/FastAPI）

| 文件 | 操作 | 说明 |
|---|---|---|
| `services/tts.py` | **新增** | Edge TTS 语音合成服务 |
| `main.py` | **修改** | WebSocket 增加 TTS 返回 + 音色 API |
| `requirements.txt` | **修改** | 添加 edge-tts 依赖 |

### 前端（Vue 3）

| 文件 | 操作 | 说明 |
|---|---|---|
| `components/DigitalTeacher/index.vue` | **新增** | Live2D 数字人渲染组件 |
| `components/AICompanion/index.vue` | **重写** | 左图右聊的数字人面板 |

### 依赖

```bash
# 后端（自动安装）
pip install edge-tts>=6.1.9

# 前端（已安装）
npm install pixi.js@7 pixi-live2d-display
```

---

## 使用步骤

### 1. 启动后端服务

```bash
cd struct-quest-backend
pip install -r requirements.txt  # 确保 edge-tts 已安装
python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload
```

后端会启动在 `http://localhost:8008`，提供以下新接口：

- `GET /api/tts/voices` - 获取可用音色列表
- `WS /ws/chat` - WebSocket 聊天（支持 TTS 参数）

### 2. 启动前端开发服务器

```bash
cd struct-quest-frontend
npm install  # 如果还没装过 pixi-live2d-display
npm run dev
```

前端会启动在 `http://localhost:5173`

### 3. 使用数字人老师

打开浏览器访问前端页面，点击悬浮球即可看到新的数字人老师面板：

#### 基础使用流程：
1. **输入问题** → 在底部输入框打字提问
2. **AI 回复** → 右侧显示流式文字输出（支持 Markdown）
3. **语音播放** → 自动合成语音并播放（可暂停/停止）
4. **口型同步** → 左侧 Live2D 形象随语音张嘴说话

#### 高级功能：
- **🎙️ 切换音色**：点击头部麦克风图标，选择 6 种中文音色
- **快捷标签**：点击预设问题快速提问
- **Markdown 渲染**：代码块、列表等格式正确显示

---

## 技术架构

```
用户输入文字
    ↓
[前端] WebSocket 发送消息（带 voice/enable_tts 参数）
    ↓
[后端] LLM 流式生成回答（chunk → chunk → ...）
    ↓        ↘
[后端] 文字 done  ←  同时 →  TTS 合成音频（base64 MP3）
    ↓                              ↓
[前端] 显示文字                  [前端] 播放音频 + 口型驱动
    ↓                              ↓
[前端] 字幕展示               [WebAudio 分析音量]
                                      ↓
                               [Live2D 更新口型参数]
```

### 关键技术点：

1. **TTS 语音合成**
   - 使用微软 Edge TTS（免费、无需 API Key）
   - 支持 6 种高质量中文音色
   - 返回 base64 编码 MP3（方便 WebSocket 传输）

2. **Live2D 渲染**
   - 基于 PixiJS v7 + pixi-live2d-display
   - 使用 Haru 官方示例模型（职业装风格）
   - 支持口型参数实时更新（ParamMouthOpenY）

3. **口型同步**
   - WebAudio API 的 AnalyserNode 获取实时音量
   - 音量值映射到 Live2D 的嘴部开合参数
   - 50ms 刷新率保证流畅度

4. **WebSocket 协议**

发送格式：
```json
{
  "messages": [...],
  "provider": "openai",
  "voice": "xiaoxiao",
  "enable_tts": true
}
```

接收格式（多种类型）：
```json
{"type": "chunk", "content": "..."}           // 流式文字
{"type": "done", "full_content": "..."}       // 文字结束
{"type": "tts_start"}                          // 开始合成语音
{"type": "tts_audio", "audio_base64": "...", "format": "mp3"}  // 音频数据
{"type": "tts_error", "message": "..."}       // TTS 错误
```

---

## 可用音色列表

| Key | 名称 | 适用场景 |
|-----|------|---------|
| `xiaoxiao` | 温柔女声 | 默认，温柔亲切讲解 |
| `yunxi` | 阳光男声 | 充满活力的教学 |
| `xiaoyi` | 知性女声 | 学术性内容讲解 |
| `yunyang` | 沉稳男声 | 严肃专业的内容 |
| `xiaobei` | 活泼女声 | 轻松愉快的氛围 |
| `xiaozhen` | 亲和女声 | 自然像朋友聊天 |

---

## 自定义配置

### 更换 Live2D 模型

编辑 `components/DigitalTeacher/index.vue` 中的 `modelUrl` 默认值：

```javascript
// 当前使用的是 Haru 模型（官方示例）
modelUrl: 'https://cdn.jsdelivr.net/gh/guansss/pixi-live2d-display/test/assets/haru/haru_gretest_t03.model3.json'

// 可以换成其他模型，例如：
modelUrl: '/models/your-custom-model.model3.json'  // 本地模型
```

推荐模型来源：
- **Hiyori** (ひよりん): https://github.com/HiyoriTera2/hiyoriv1-live2d
- **Mark**: 官方示例男性角色
- **自定义**: 用 Live2D Cubism Editor 制作

### 调整面板尺寸

在 `AICompanion/index.vue` 的样式中修改 `.digital-teacher-panel` 的 `min-height` 和 `.teacher-visual` 的 `width`。

---

## 注意事项

1. **首次加载较慢**：Live2D 模型文件较大（几 MB~几十 MB），首次需要从 CDN 下载
2. **浏览器兼容**：需要现代浏览器（Chrome 80+、Firefox 75+、Safari 14+）支持 WebGL
3. **自动播放策略**：浏览器的自动播放策略可能阻止音频自动播放，需要用户先有一次交互操作
4. **网络延迟**：TTS 合成时间取决于文本长度（通常 500 字以内 1-2 秒）

---

## 下一步优化方向

- [ ] 添加更多 Live2D 表情动作（点头、摇头、眨眼等）
- [ ] 接入 D-ID 或 MuseTalk 实现更逼真的数字人
- [ ] 支持用户上传自定义头像/照片作为数字人基础
- [ ] 添加语气风格 System Prompt 注入（让 AI 回复风格随音色变化）
- [ ] 语音识别输入（STT），实现完全语音对话
- [ ] 离线 TTS 方案（如 Coqui TTS 或 VITS）避免网络依赖
