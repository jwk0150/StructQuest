# D-ID 数字人视频 — 配置与使用指南

## 🎬 功能说明

D-ID 是业界领先的 AI 数字人视频生成服务，可以：
- ✅ 输入文字 → 生成**真人级数字人说话视频**
- ✅ **完美口型同步**（音素级别）
- ✅ **自动缓存**（相同文本不重复计费！）
- ✅ 多种形象 + 中文音色

### 与免费 Edge TTS 的区别

| | Edge TTS（默认） | D-ID |
|---|---|---|
| **效果** | 只有声音，无画面 | **真人脸 + 语音 + 口型同步** |
| **费用** | 完全免费 | 按分钟付费（约 $0.05/个视频） |
| **速度** | 即时（<1秒） | 几秒~几十秒生成 |
| **缓存** | 无 | **有（重复文本不花钱）** |

---

## 🚀 快速配置（3 步）

### 第 1 步：注册 D-ID 账号

1. 访问 https://studio.d-id.com/
2. 注册账号（可用 Google / GitHub 登录）
3. 进入 Dashboard，可以看到免费试用额度

### 第 2 步：获取 API Key

1. 在页面右上角点击 **Account**
2. 选择 **API Keys** 标签
3. 点击 **Create API Key** 复制生成的 Key
4. 填入 `.env` 文件：

```bash
# .env
DID_API_KEY=你的API_KEY粘贴在这里
```

### 第 3 步：重启后端

```bash
# 重启后端使 API Key 生效
cd struct-quest-backend
python -m uvicorn app.main:app --port 8008 --reload
```

---

## 🎮 使用方式

### 切换模式

在数字人老师面板的头部，有一个切换按钮：

```
[🧑🏫数字人老师] [🔊→🎬] [🎙️] [✕]
                  ↑
           点击切换 TTS/D-ID 模式
```

- **🔊 模式**：Edge TTS 免费语音 + CSS 卡通形象
- **🎬 模式**：D-ID 真实数字人视频

### 缓存机制（重要！）

```
第1次提问 "解释一下链表"
    ↓
┌─ 后端计算文本 hash ─────────────┐
│  hash("解释一下链表...") = abc123 │
└───────────────────────────────┘
    ↓
  查本地缓存目录: static/videos/did/
    ├── 有: did_abc123_xiaoxiao.mp4 ✅ 直接返回 URL (不调 API!)
    └── 没有: 
        ↓
    调 D-API 生成 (~10-20s)
        ↓
    下载视频 → 保存到本地
        ↓
    返回 URL 给前端播放
        ↓
    下次问同样的问题 → 直接用缓存！💰 不再扣费!
```

**关键点：只要输入的文字完全一样，就永远只付一次钱！**

### 缓存文件位置

```
struct-quest-backend/app/static/videos/did/
├── did_abc123_xiaoxiao.mp4      # 第1次回答"链表"的视频（已缓存）
├── did_def456_yunxi.mp4          # 另一个问题+不同音色的视频
└── ...
```

缓存目录会随 Docker volume 持久化保存。

---

## 📋 可用形象列表

| Key | 名称 | 说明 |
|-----|------|------|
| `teacher_female` | 女老师（Emma） | 默认，职业装女性 |
| `teacher_male` | 男老师（James） | 职业装男性 |
| `emma` | Emma v2 | 官方示例女性 |
| `james` | James v2 | 官方示例男性 |
| `amy` | Amy v2 | 年轻女性 |
| `alex` | Alex v2 | 年轻男性 |

### 自定义形象（进阶）

你可以在 https://studio.d-id.com/ 上传自己的照片或选择更多预设形象，然后使用该形象的 `source_url`：

1. 在 Studio 中选择/上传一个形象
2. 复制该形象的图片 URL 或使用其 ID
3. 在 `services/did.py` 的 `AVATARS` 字典中添加新条目

---

## 🗣️ 可用音色列表

| Key | 名称 | 语言 |
|-----|------|------|
| `xiaoxiao` | 温柔女声 | 中文 |
| `yunxi` | 阳光男声 | 中文 |
| `xiaoyi` | 知性女声 | 中文 |
| `yunyang` | 沉稳男声 | 中文 |
| `xiaobei` | 活泼女声 | 中文 |
| `xiaozhen` | 亲和女声 | 中文 |
| `en_female` | Jenny | 英文 |
| `en_male` | Guy | 英文 |

---

## 🔧 API 接口参考

### 检查 D-ID 服务状态

```bash
GET /api/did/status
# 返回: { available, remaining_credits, total_used }
```

### 获取可用形象

```bash
GET /api/did/avatars
# 返回: { emma: { name, url }, james: { name, url }, ... }
```

### 手动生成视频

```bash
POST /api/did/generate
Body: {
  text: "要讲解的文本",
  voice: "xiaoxiao",          // 音色
  avatar: "teacher_female",   // 形象
  use_cache: true              // 是否启用缓存
}
# 返回:
{
  video_url: "/static/videos/did/did_xxx.mp4",
  is_cached: false,
  file_name: "did_xxx_xiaoxiao.mp4",
  duration: 12.5,
  message: "视频生成完成并已缓存"
}
```

### WebSocket 自动集成

当 `tts_mode=did` 时，WebSocket `/ws/chat` 会自动在 LLM 回复完成后调用 D-ID 生成视频并返回：

```json
// 发送（前端 → 后端）
{
  "messages": [...],
  "tts_mode": "did",
  "voice": "xiaoxiao",
  "avatar": "teacher_female",
  "enable_tts": true
}

// 收到（后端 → 前端）
{ "type": "tts_start", "mode": "did" }
{ "type": "did_video", "video_url": "/static/videos/did/did_xxx.mp4", "is_cached": false }
```

---

## 💰 费用说明

| 项目 | 价格 | 备注 |
|------|------|------|
| 新建账号 | **免费 $25 额度** | 可生成约 500 个短视频 |
| 每个视频（30s 内） | ~5 credits | 取决于视频时长 |
| 缓存命中 | **$0** | 同样文字不重复收费 |

### 省费技巧

1. **开启缓存**（默认开启）：相同回答不重新生成
2. **控制文本长度**：后端限制 500 字符以内
3. **优先用 Edge TTS**：不需要真人效果时用免费模式
4. **批量生成**：可以把常见问题预先生成好

---

## ⚠️ 注意事项

1. **首次加载较慢**：D-ID 视频需要几秒~几十秒生成时间
2. **需要网络**：视频生成依赖 D-ID 云端服务
3. **API Key 安全**：不要把 `.env` 提交到 Git
4. **额度监控**：可调用 `/api/did/status` 查看剩余额度

---

## ❓ 常见问题

**Q: 不配置 DID_API_KEY 能用吗？**
A: 能！系统会自动降级到免费的 Edge TTS + CSS 卡通形象模式。

**Q: 缓存的视频会过期吗？**
A: 不会。缓存在本地磁盘上永久有效，除非手动删除。

**Q: 如何清除缓存？**
A: 删除 `static/videos/did/` 目录下的文件即可。

**Q: 可以用自己的照片做数字人吗？**
A: 可以！在 D-ID Studio 上传照片后获取 source_url，添加到 `AVATARS` 字典中即可。
