/**
 * 数字人主应用逻辑
 * - SSE 流式对话
 * - 逐句 TTS 语音合成 + 唇形同步
 * - 语音输入 (Web Speech API)
 * - 音色切换与性别匹配
 */

// ═══════════════════════════════════════════
// 状态管理
// ═══════════════════════════════════════════
const App = {
    avatar: null,
    chatHistory: [],
    isResponding: false,
    ttsEnabled: true,
    micEnabled: false,
    currentVoice: "xiaoxiao",
    audioContext: null,
    analyser: null,
    audioQueue: [],
    isPlayingAudio: false,
    recognition: null,
    waveformBars: [],
};

// ═══════════════════════════════════════════
// DOM 引用
// ═══════════════════════════════════════════
const $ = (id) => document.getElementById(id);
const elements = {};

// ═══════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════
function init() {
    // 缓存 DOM
    ["avatarCanvas", "statusBadge", "statusDot", "statusText", "waveform",
     "voiceSelect", "ttsToggle", "micToggle", "chatMessages", "chatInput",
     "sendBtn", "clearBtn"].forEach(id => {
        elements[id] = $(id);
    });

    // 初始化数字人
    App.avatar = new DigitalAvatar(elements.avatarCanvas);

    // 初始化波形可视化
    initWaveform();

    // 音色切换 → 同步数字人性别
    elements.voiceSelect.addEventListener("change", (e) => {
        App.currentVoice = e.target.value;
        const isMale = ["yunxi", "yunyang", "yunjian"].includes(e.target.value);
        App.avatar.setGender(isMale ? "male" : "female");
    });

    // TTS 开关
    elements.ttsToggle.addEventListener("click", () => {
        App.ttsEnabled = !App.ttsEnabled;
        elements.ttsToggle.classList.toggle("active", App.ttsEnabled);
        if (!App.ttsEnabled) {
            stopAllAudio();
        }
    });

    // 麦克风开关
    elements.micToggle.addEventListener("click", toggleMic);

    // 发送消息
    elements.sendBtn.addEventListener("click", sendMessage);
    elements.chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 清空对话
    elements.clearBtn.addEventListener("click", () => {
        if (confirm("确定清空所有对话？")) {
            App.chatHistory = [];
            elements.chatMessages.innerHTML = "";
            addMessage("ai", "对话已清空，我们重新开始吧~");
        }
    });

    // 自动聚焦输入框
    elements.chatInput.focus();

    // 初始化语音识别（如果浏览器支持）
    initSpeechRecognition();
}

// ═══════════════════════════════════════════
// 波形可视化
// ═══════════════════════════════════════════
function initWaveform() {
    const container = elements.waveform;
    for (let i = 0; i < 24; i++) {
        const bar = document.createElement("div");
        bar.className = "wave-bar";
        bar.style.height = "4px";
        container.appendChild(bar);
        App.waveformBars.push(bar);
    }
}

function updateWaveform(amplitude) {
    App.waveformBars.forEach((bar, i) => {
        const center = App.waveformBars.length / 2;
        const distance = Math.abs(i - center);
        const wave = Math.sin(Date.now() * 0.01 + i * 0.5) * 0.5 + 0.5;
        const height = 4 + amplitude * (35 - distance * 2) * wave;
        bar.style.height = `${Math.max(4, height)}px`;
    });
}

// ═══════════════════════════════════════════
// 状态切换
// ═══════════════════════════════════════════
function setStatus(state, text) {
    elements.statusBadge.className = `status-badge ${state}`;
    elements.statusText.textContent = text;
    App.avatar.setState(state);

    if (state !== "speaking") {
        elements.waveform.classList.remove("active");
    }
}

// ═══════════════════════════════════════════
// 消息渲染
// ═══════════════════════════════════════════
function addMessage(role, content) {
    const msg = document.createElement("div");
    msg.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "ai" ? "智" : "我";

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    const p = document.createElement("p");
    p.textContent = content;
    contentDiv.appendChild(p);

    msg.appendChild(avatar);
    msg.appendChild(contentDiv);
    elements.chatMessages.appendChild(msg);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return { contentDiv, p };
}

function addTypingIndicator() {
    const msg = document.createElement("div");
    msg.className = "message ai";
    msg.id = "typingMsg";

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = "智";

    const content = document.createElement("div");
    content.className = "message-content";
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    indicator.innerHTML = "<span></span><span></span><span></span>";
    content.appendChild(indicator);

    msg.appendChild(avatar);
    msg.appendChild(content);
    elements.chatMessages.appendChild(msg);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typing = document.getElementById("typingMsg");
    if (typing) typing.remove();
}

// ═══════════════════════════════════════════
// 发送消息 & SSE 流式接收
// ═══════════════════════════════════════════
async function sendMessage() {
    const text = elements.chatInput.value.trim();
    if (!text || App.isResponding) return;

    // 添加用户消息
    addMessage("user", text);
    App.chatHistory.push({ role: "user", content: text });

    // 清空输入框
    elements.chatInput.value = "";
    elements.sendBtn.disabled = true;
    App.isResponding = true;

    // 显示打字指示器
    addTypingIndicator();

    // 数字人进入思考状态
    setStatus("thinking", "思考中...");

    // 准备流式接收
    let fullResponse = "";
    let sentenceBuffer = "";
    let responseElement = null;
    let ttsQueue = [];

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                history: App.chatHistory.slice(-10),
            }),
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        removeTypingIndicator();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = line.slice(6);
                try {
                    const parsed = JSON.parse(data);

                    if (parsed.type === "token") {
                        // 首个 token 到达 → 切换为回答状态
                        if (!responseElement) {
                            responseElement = addMessage("ai", "");
                            setStatus("idle", "回答中");
                        }

                        fullResponse += parsed.content;
                        responseElement.p.textContent = fullResponse;
                        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

                        // 句子分割 → TTS 队列
                        sentenceBuffer += parsed.content;
                        const sentences = splitSentences(sentenceBuffer);
                        if (sentences.complete.length > 0) {
                            for (const s of sentences.complete) {
                                if (s.trim()) {
                                    ttsQueue.push(s.trim());
                                    // 如果 TTS 没在播放，开始播放
                                    if (!App.isPlayingAudio && App.ttsEnabled) {
                                        processTTSQueue(ttsQueue);
                                    }
                                }
                            }
                            sentenceBuffer = sentences.remaining;
                        }
                    } else if (parsed.type === "done") {
                        // 处理剩余文本
                        if (sentenceBuffer.trim()) {
                            ttsQueue.push(sentenceBuffer.trim());
                            if (!App.isPlayingAudio && App.ttsEnabled) {
                                processTTSQueue(ttsQueue);
                            }
                        }
                    } else if (parsed.type === "error") {
                        if (!responseElement) {
                            responseElement = addMessage("ai", "");
                        }
                        fullResponse = parsed.content;
                        responseElement.p.textContent = fullResponse;
                    }
                } catch (e) {
                    // JSON 解析失败，跳过
                }
            }
        }

        // 记录到历史
        if (fullResponse) {
            App.chatHistory.push({ role: "assistant", content: fullResponse });
        }

        // 如果 TTS 未开启或没有音频要播放，直接恢复 idle
        if (!App.ttsEnabled || ttsQueue.length === 0) {
            setStatus("idle", "待命中");
        } else {
            // 等待 TTS 队列播放完毕
            const checkInterval = setInterval(() => {
                if (!App.isPlayingAudio && ttsQueue.length === 0) {
                    clearInterval(checkInterval);
                    setStatus("idle", "待命中");
                }
            }, 200);
        }

    } catch (error) {
        console.error("发送失败:", error);
        removeTypingIndicator();
        addMessage("ai", "抱歉，连接出了点问题，请稍后再试。");
        setStatus("idle", "待命中");
    } finally {
        elements.sendBtn.disabled = false;
        App.isResponding = false;
    }
}

// ═══════════════════════════════════════════
// 句子分割
// ═══════════════════════════════════════════
function splitSentences(text) {
    const pattern = /[^。！？.!?\n]+[。！？.!?\n]+/g;
    const complete = text.match(pattern) || [];
    const consumed = complete.join("");
    const remaining = text.slice(consumed.length);
    return { complete, remaining };
}

// ═══════════════════════════════════════════
// TTS 语音合成 & 唇形同步
// ═══════════════════════════════════════════
async function processTTSQueue(queue) {
    if (App.isPlayingAudio || queue.length === 0) return;

    const text = queue.shift();
    if (!text || text.length < 1) return;

    App.isPlayingAudio = true;

    try {
        const resp = await fetch("/api/tts", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, voice: App.currentVoice }),
        });

        if (!resp.ok) throw new Error("TTS 请求失败");

        const blob = await resp.blob();
        const arrayBuffer = await blob.arrayBuffer();

        await playAudioWithLipSync(arrayBuffer);

    } catch (error) {
        console.error("TTS 失败:", error);
    } finally {
        App.isPlayingAudio = false;

        // 播放下一条
        if (queue.length > 0 && App.ttsEnabled) {
            processTTSQueue(queue);
        }
    }
}

async function playAudioWithLipSync(arrayBuffer) {
    // 确保 AudioContext 存在
    if (!App.audioContext) {
        App.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    // 如果 context 被挂起（浏览器策略），恢复它
    if (App.audioContext.state === "suspended") {
        await App.audioContext.resume();
    }

    // 解码音频
    const audioBuffer = await App.audioContext.decodeAudioData(arrayBuffer);

    // 创建播放源
    const source = App.audioContext.createBufferSource();
    source.buffer = audioBuffer;

    // 创建分析器（用于唇形同步）
    App.analyser = App.audioContext.createAnalyser();
    App.analyser.fftSize = 256;
    App.analyser.smoothingTimeConstant = 0.6;

    // 连接：source → analyser → destination
    source.connect(App.analyser);
    App.analyser.connect(App.audioContext.destination);

    // 切换到说话状态
    setStatus("speaking", "正在回答");
    elements.waveform.classList.add("active");

    // 启动唇形同步循环
    const freqData = new Uint8Array(App.analyser.frequencyBinCount);
    let lipSyncActive = true;

    const lipSyncLoop = () => {
        if (!lipSyncActive) return;
        App.analyser.getByteFrequencyData(freqData);

        // 计算低频段振幅（人声主要频段）
        let sum = 0;
        const voiceRange = Math.min(30, freqData.length);
        for (let i = 0; i < voiceRange; i++) {
            sum += freqData[i];
        }
        const amplitude = (sum / voiceRange) / 255;

        // 驱动嘴部动画
        App.avatar.setMouthAmplitude(amplitude);
        updateWaveform(amplitude);

        requestAnimationFrame(lipSyncLoop);
    };
    lipSyncLoop();

    // 播放音频
    return new Promise((resolve) => {
        source.onended = () => {
            lipSyncActive = false;
            App.avatar.setMouthAmplitude(0);
            elements.waveform.classList.remove("active");
            resolve();
        };
        source.start(0);
    });
}

function stopAllAudio() {
    App.audioQueue = [];
    App.isPlayingAudio = false;
    App.avatar.setMouthAmplitude(0);
    elements.waveform.classList.remove("active");
    if (App.audioContext) {
        // 不能直接关闭 context，否则后续无法播放
        // 只是停止当前播放
    }
}

// ═══════════════════════════════════════════
// 语音输入 (Web Speech API)
// ═══════════════════════════════════════════
function initSpeechRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        console.log("浏览器不支持语音识别");
        return;
    }

    App.recognition = new SR();
    App.recognition.lang = "zh-CN";
    App.recognition.continuous = false;
    App.recognition.interimResults = true;

    let finalText = "";

    App.recognition.onstart = () => {
        document.body.classList.add("recording");
        elements.chatInput.placeholder = "正在聆听...请说话";
        setStatus("listening", "聆听中...");
    };

    App.recognition.onresult = (event) => {
        let interim = "";
        finalText = "";
        for (let i = 0; i < event.results.length; i++) {
            if (event.results[i].isFinal) {
                finalText += event.results[i][0].transcript;
            } else {
                interim += event.results[i][0].transcript;
            }
        }
        elements.chatInput.value = finalText + interim;
    };

    App.recognition.onerror = (event) => {
        console.error("语音识别错误:", event.error);
        document.body.classList.remove("recording");
        elements.chatInput.placeholder = "输入消息，或点击麦克风语音对话...";
        setStatus("idle", "待命中");
    };

    App.recognition.onend = () => {
        document.body.classList.remove("recording");
        elements.chatInput.placeholder = "输入消息，或点击麦克风语音对话...";
        if (finalText.trim()) {
            sendMessage();
        } else {
            setStatus("idle", "待命中");
        }
    };
}

function toggleMic() {
    if (!App.recognition) {
        alert("您的浏览器不支持语音识别，请使用 Chrome 或 Edge 浏览器。");
        return;
    }

    if (App.micEnabled) {
        App.recognition.stop();
        App.micEnabled = false;
        elements.micToggle.classList.remove("active");
    } else {
        try {
            App.recognition.start();
            App.micEnabled = true;
            elements.micToggle.classList.add("active");
        } catch (e) {
            console.error("启动语音识别失败:", e);
        }
    }
}

// ═══════════════════════════════════════════
// 启动
// ═══════════════════════════════════════════
window.addEventListener("DOMContentLoaded", init);
