/**
 * 数字人 Canvas 引擎
 * 绘制一个半写实风格的虚拟人像，支持：
 * - 自然眨眼
 * - 眼球跟随鼠标
 * - 说话时嘴部动画（唇形同步）
 * - 微表情与头部摆动
 * - 状态切换（idle / listening / thinking / speaking）
 */
class DigitalAvatar {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d");
        this.W = canvas.width;
        this.H = canvas.height;

        // 动画状态
        this.state = "idle";
        this.time = 0;
        this.mouseX = this.W / 2;
        this.mouseY = this.H / 2;

        // 面部参数（基于中心点）
        this.cx = this.W / 2;
        this.cy = this.H * 0.48;

        // 眼睛
        this.eyeOffsetX = 0;
        this.eyeOffsetY = 0;
        this.blinkProgress = 0; // 0=睁开, 1=闭合
        this.nextBlinkTime = 2 + Math.random() * 3;
        this.blinkTimer = 0;

        // 嘴部
        this.mouthOpen = 0; // 0=闭合, 1=全开
        this.targetMouthOpen = 0;
        this.mouthWidth = 0.16;
        this.smileAmount = 0.3;

        // 头部摆动
        this.headTiltX = 0;
        this.headTiltY = 0;
        this.headSway = 0;

        // 呼吸
        this.breathPhase = 0;

        // 表情
        this.eyebrowRaise = 0;
        this.eyeSquint = 0;

        // 配色（女声默认偏柔和）
        this.colors = this.femaleColors();

        // 鼠标跟随
        this._onMouseMove = (e) => {
            const rect = canvas.getBoundingClientRect();
            const scaleX = this.W / rect.width;
            const scaleY = this.H / rect.height;
            this.mouseX = (e.clientX - rect.left) * scaleX;
            this.mouseY = (e.clientY - rect.top) * scaleY;
        };
        window.addEventListener("mousemove", this._onMouseMove);

        this.start();
    }

    // ═══ 配色方案 ═══
    femaleColors() {
        return {
            skinLight: "#fce4d6",
            skinMid: "#f0c8a8",
            skinShadow: "#d9a884",
            skinDeep: "#c08866",
            hairDark: "#3a2820",
            hairMid: "#5c3d2e",
            hairLight: "#7a5340",
            hairHighlight: "#9a6b50",
            eyeWhite: "#f8f6f3",
            iris: "#6b4e3a",
            irisRing: "#4a3525",
            pupil: "#1a1208",
            lip: "#d4707a",
            lipDeep: "#b85a66",
            lipLight: "#e89098",
            blush: "#f4a8a8",
            brow: "#4a3525",
            noseShadow: "#e0b098",
            bg: null, // 透明背景
            clothing: "#4a3d8f",
            clothingLight: "#5c4da8",
        };
    }

    maleColors() {
        return {
            skinLight: "#f5d5b8",
            skinMid: "#e8c0a0",
            skinShadow: "#c89878",
            skinDeep: "#a87858",
            hairDark: "#1a1510",
            hairMid: "#2a2218",
            hairLight: "#3a3020",
            hairHighlight: "#4a3d28",
            eyeWhite: "#f8f6f3",
            iris: "#4a3525",
            irisRing: "#3a2515",
            pupil: "#0a0805",
            lip: "#c47068",
            lipDeep: "#a85850",
            lipLight: "#d48880",
            blush: "#e8a098",
            brow: "#2a2218",
            noseShadow: "#d8a888",
            bg: null,
            clothing: "#2a3560",
            clothingLight: "#3a4578",
        };
    }

    setGender(gender) {
        this.colors = gender === "male" ? this.maleColors() : this.femaleColors();
    }

    // ═══ 状态切换 ═══
    setState(state) {
        this.state = state;
        switch (state) {
            case "idle":
                this.targetMouthOpen = 0;
                this.smileAmount = 0.3;
                this.eyebrowRaise = 0;
                this.eyeSquint = 0;
                break;
            case "listening":
                this.targetMouthOpen = 0;
                this.smileAmount = 0.15;
                this.eyebrowRaise = 0.08;
                this.eyeSquint = 0.05;
                break;
            case "thinking":
                this.targetMouthOpen = 0;
                this.smileAmount = 0;
                this.eyebrowRaise = 0.15;
                this.eyeSquint = 0.1;
                break;
            case "speaking":
                this.smileAmount = 0.25;
                this.eyebrowRaise = 0.05;
                this.eyeSquint = 0;
                break;
        }
    }

    // 设置嘴部张开度（用于唇形同步）
    setMouthAmplitude(amp) {
        // amp: 0~1 音频振幅
        if (this.state === "speaking") {
            this.targetMouthOpen = Math.min(1, amp * 1.5);
        }
    }

    // ═══ 主循环 ═══
    start() {
        let lastTime = performance.now();
        const loop = (now) => {
            const dt = Math.min(0.05, (now - lastTime) / 1000);
            lastTime = now;
            this.update(dt);
            this.draw();
            requestAnimationFrame(loop);
        };
        requestAnimationFrame(loop);
    }

    // ═══ 更新逻辑 ═══
    update(dt) {
        this.time += dt;

        // 眨眼逻辑
        this.blinkTimer += dt;
        if (this.blinkTimer >= this.nextBlinkTime && this.blinkProgress === 0) {
            this.blinkProgress = 0.01; // 开始眨眼
        }
        if (this.blinkProgress > 0) {
            if (this.blinkProgress < 0.5) {
                this.blinkProgress += dt * 12; // 闭眼速度
            } else {
                this.blinkProgress += dt * 8; // 睁眼速度
            }
            if (this.blinkProgress >= 1) {
                this.blinkProgress = 0;
                this.blinkTimer = 0;
                this.nextBlinkTime = 2.5 + Math.random() * 3.5;
            }
        }

        // 嘴部平滑过渡
        this.mouthOpen += (this.targetMouthOpen - this.mouthOpen) * dt * 12;
        // 说话时嘴部有微小抖动
        if (this.state === "speaking" && this.targetMouthOpen > 0.01) {
            this.mouthOpen += Math.sin(this.time * 25) * 0.02 * this.targetMouthOpen;
        }

        // 眼球跟随鼠标
        const dx = (this.mouseX - this.cx) / this.W;
        const dy = (this.mouseY - this.cy) / this.H;
        const maxOffset = 8;
        this.eyeOffsetX += (dx * maxOffset - this.eyeOffsetX) * dt * 5;
        this.eyeOffsetY += (dy * maxOffset - this.eyeOffsetY) * dt * 5;

        // 头部微摆（呼吸节奏 + 随机摆动）
        this.breathPhase += dt;
        this.headSway = Math.sin(this.breathPhase * 0.8) * 3;

        // thinking 状态头微倾
        if (this.state === "thinking") {
            this.headTiltX += (Math.sin(this.time * 0.5) * 4 + 6 - this.headTiltX) * dt * 3;
            this.headTiltY += (-8 - this.headTiltY) * dt * 3;
        } else if (this.state === "listening") {
            this.headTiltX += (3 - this.headTiltX) * dt * 3;
            this.headTiltY += (2 - this.headTiltY) * dt * 3;
        } else {
            this.headTiltX += (this.headSway - this.headTiltX) * dt * 2;
            this.headTiltY += (Math.sin(this.breathPhase * 0.6) * 2 - this.headTiltY) * dt * 2;
        }
    }

    // ═══ 绘制 ═══
    draw() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.W, this.H);

        ctx.save();
        // 整体平移到中心，应用头部摆动
        ctx.translate(this.cx + this.headTiltX, this.cy + this.headTiltY);
        // 整体呼吸缩放
        const breathScale = 1 + Math.sin(this.breathPhase * 1.2) * 0.005;
        ctx.scale(breathScale, breathScale);

        // 按层次绘制
        this.drawShoulders(ctx);
        this.drawNeck(ctx);
        this.drawHairBack(ctx);
        this.drawFace(ctx);
        this.drawEars(ctx);
        this.drawNose(ctx);
        this.drawBlush(ctx);
        this.drawEyebrows(ctx);
        this.drawEyes(ctx);
        this.drawMouth(ctx);
        this.drawHairFront(ctx);

        ctx.restore();
    }

    // ═══ 肩膀/衣服 ═══
    drawShoulders(ctx) {
        const c = this.colors;
        const grad = ctx.createLinearGradient(0, 180, 0, 300);
        grad.addColorStop(0, c.clothingLight);
        grad.addColorStop(1, c.clothing);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(-200, 300);
        ctx.lineTo(-200, 210);
        ctx.bezierCurveTo(-160, 180, -90, 170, 0, 168);
        ctx.bezierCurveTo(90, 170, 160, 180, 200, 210);
        ctx.lineTo(200, 300);
        ctx.closePath();
        ctx.fill();

        // 衣领
        ctx.fillStyle = "rgba(0,0,0,0.15)";
        ctx.beginPath();
        ctx.moveTo(-50, 170);
        ctx.bezierCurveTo(-30, 180, 30, 180, 50, 170);
        ctx.lineTo(40, 165);
        ctx.bezierCurveTo(20, 172, -20, 172, -40, 165);
        ctx.closePath();
        ctx.fill();
    }

    // ═══ 脖子 ═══
    drawNeck(ctx) {
        const c = this.colors;
        const grad = ctx.createLinearGradient(-40, 120, 40, 175);
        grad.addColorStop(0, c.skinShadow);
        grad.addColorStop(0.5, c.skinMid);
        grad.addColorStop(1, c.skinLight);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(-38, 120);
        ctx.bezierCurveTo(-35, 145, -32, 160, -30, 172);
        ctx.lineTo(30, 172);
        ctx.bezierCurveTo(32, 160, 35, 145, 38, 120);
        ctx.closePath();
        ctx.fill();

        // 脖子阴影
        ctx.fillStyle = "rgba(0,0,0,0.08)";
        ctx.beginPath();
        ctx.ellipse(0, 125, 40, 12, 0, 0, Math.PI);
        ctx.fill();
    }

    // ═══ 后方头发 ═══
    drawHairBack(ctx) {
        const c = this.colors;
        const grad = ctx.createRadialGradient(0, -20, 20, 0, 0, 160);
        grad.addColorStop(0, c.hairMid);
        grad.addColorStop(0.7, c.hairDark);
        grad.addColorStop(1, c.hairDark);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.ellipse(0, 0, 155, 175, 0, 0, Math.PI * 2);
        ctx.fill();
    }

    // ═══ 脸部 ═══
    drawFace(ctx) {
        const c = this.colors;
        // 脸部椭圆
        const grad = ctx.createRadialGradient(-20, -30, 30, 0, 10, 140);
        grad.addColorStop(0, c.skinLight);
        grad.addColorStop(0.6, c.skinMid);
        grad.addColorStop(1, c.skinShadow);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.ellipse(0, 0, 105, 130, 0, 0, Math.PI * 2);
        ctx.fill();

        // 脸部侧面阴影
        ctx.fillStyle = "rgba(0,0,0,0.06)";
        ctx.beginPath();
        ctx.ellipse(70, 10, 35, 110, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.ellipse(-70, 10, 35, 110, 0, 0, Math.PI * 2);
        ctx.fill();

        // 额头高光
        const hlGrad = ctx.createRadialGradient(0, -70, 5, 0, -50, 60);
        hlGrad.addColorStop(0, "rgba(255,245,235,0.4)");
        hlGrad.addColorStop(1, "rgba(255,245,235,0)");
        ctx.fillStyle = hlGrad;
        ctx.beginPath();
        ctx.ellipse(0, -60, 55, 35, 0, 0, Math.PI * 2);
        ctx.fill();
    }

    // ═══ 耳朵 ═══
    drawEars(ctx) {
        const c = this.colors;
        for (const side of [-1, 1]) {
            ctx.save();
            ctx.translate(side * 98, 5);
            ctx.fillStyle = c.skinMid;
            ctx.beginPath();
            ctx.ellipse(0, 0, 16, 28, 0, 0, Math.PI * 2);
            ctx.fill();
            // 耳廓阴影
            ctx.fillStyle = c.skinShadow;
            ctx.beginPath();
            ctx.ellipse(side * 3, 2, 8, 18, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    // ═══ 鼻子 ═══
    drawNose(ctx) {
        const c = this.colors;
        // 鼻梁侧面
        ctx.fillStyle = c.noseShadow;
        ctx.beginPath();
        ctx.moveTo(2, -25);
        ctx.bezierCurveTo(5, -10, 8, 15, 4, 30);
        ctx.bezierCurveTo(0, 35, -5, 35, -3, 30);
        ctx.bezierCurveTo(-8, 15, -5, -10, -2, -25);
        ctx.closePath();
        ctx.fill();

        // 鼻头
        const noseGrad = ctx.createRadialGradient(0, 28, 2, 0, 30, 15);
        noseGrad.addColorStop(0, c.skinLight);
        noseGrad.addColorStop(1, c.skinMid);
        ctx.fillStyle = noseGrad;
        ctx.beginPath();
        ctx.ellipse(0, 30, 12, 10, 0, 0, Math.PI * 2);
        ctx.fill();

        // 鼻孔
        ctx.fillStyle = "rgba(0,0,0,0.12)";
        ctx.beginPath();
        ctx.ellipse(-6, 33, 3, 2.5, -0.3, 0, Math.PI * 2);
        ctx.ellipse(6, 33, 3, 2.5, 0.3, 0, Math.PI * 2);
        ctx.fill();

        // 鼻梁高光
        ctx.fillStyle = "rgba(255,240,225,0.3)";
        ctx.beginPath();
        ctx.ellipse(-3, -10, 2.5, 20, 0.05, 0, Math.PI * 2);
        ctx.fill();
    }

    // ═══ 腮红 ═══
    drawBlush(ctx) {
        if (this.state === "speaking" || this.state === "idle") {
            const c = this.colors;
            ctx.fillStyle = `rgba(244,168,168,${this.state === "speaking" ? 0.25 : 0.15})`;
            ctx.beginPath();
            ctx.ellipse(-55, 40, 22, 14, -0.2, 0, Math.PI * 2);
            ctx.ellipse(55, 40, 22, 14, 0.2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    // ═══ 眉毛 ═══
    drawEyebrows(ctx) {
        const c = this.colors;
        const raise = this.eyebrowRaise * 12;
        ctx.strokeStyle = c.brow;
        ctx.lineWidth = 7;
        ctx.lineCap = "round";

        for (const side of [-1, 1]) {
            ctx.save();
            ctx.translate(side * 42, -45 - raise);
            ctx.beginPath();
            ctx.moveTo(-22 * side, 5);
            ctx.bezierCurveTo(-15 * side, -3, -5 * side, -5, 5 * side, -2);
            ctx.bezierCurveTo(12 * side, 0, 18 * side, 3, 22 * side, 6);
            ctx.stroke();
            ctx.restore();
        }
    }

    // ═══ 眼睛 ═══
    drawEyes(ctx) {
        const c = this.colors;
        const eyeY = -20;
        const eyeSpacing = 42;
        const eyeW = 30;
        const eyeH = 18;
        const blink = this.blinkProgress;
        const squint = this.eyeSquint;

        for (const side of [-1, 1]) {
            ctx.save();
            ctx.translate(side * eyeSpacing, eyeY);

            // 眼眶区域裁剪
            ctx.save();
            ctx.beginPath();
            const currentEyeH = eyeH * (1 - blink) * (1 - squint * 0.5);
            ctx.ellipse(0, 0, eyeW, Math.max(0.5, currentEyeH), 0, 0, Math.PI * 2);
            ctx.clip();

            // 眼白
            ctx.fillStyle = c.eyeWhite;
            ctx.beginPath();
            ctx.ellipse(0, 0, eyeW, eyeH, 0, 0, Math.PI * 2);
            ctx.fill();

            if (blink < 0.85) {
                // 虹膜
                const irisX = this.eyeOffsetX * 0.6;
                const irisY = this.eyeOffsetY * 0.5;
                const irisR = 13;

                // 虹膜外圈
                const irisGrad = ctx.createRadialGradient(irisX, irisY, 2, irisX, irisY, irisR);
                irisGrad.addColorStop(0, c.iris);
                irisGrad.addColorStop(0.7, c.irisRing);
                irisGrad.addColorStop(1, c.pupil);
                ctx.fillStyle = irisGrad;
                ctx.beginPath();
                ctx.arc(irisX, irisY, irisR, 0, Math.PI * 2);
                ctx.fill();

                // 虹膜纹理线
                ctx.strokeStyle = "rgba(0,0,0,0.15)";
                ctx.lineWidth = 0.5;
                for (let i = 0; i < 12; i++) {
                    const angle = (i / 12) * Math.PI * 2;
                    ctx.beginPath();
                    ctx.moveTo(irisX + Math.cos(angle) * 4, irisY + Math.sin(angle) * 4);
                    ctx.lineTo(irisX + Math.cos(angle) * irisR, irisY + Math.sin(angle) * irisR);
                    ctx.stroke();
                }

                // 瞳孔
                ctx.fillStyle = c.pupil;
                ctx.beginPath();
                ctx.arc(irisX, irisY, 6, 0, Math.PI * 2);
                ctx.fill();

                // 高光
                ctx.fillStyle = "rgba(255,255,255,0.9)";
                ctx.beginPath();
                ctx.arc(irisX - 4, irisY - 4, 3.5, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = "rgba(255,255,255,0.5)";
                ctx.beginPath();
                ctx.arc(irisX + 3, irisY + 3, 1.5, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.restore(); // 取消裁剪

            // 上眼线
            ctx.strokeStyle = "rgba(40,25,15,0.6)";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.ellipse(0, 0, eyeW, currentEyeH, 0, Math.PI, Math.PI * 2);
            ctx.stroke();

            // 下眼线
            ctx.strokeStyle = "rgba(40,25,15,0.2)";
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.ellipse(0, 1, eyeW, currentEyeH, 0, 0, Math.PI);
            ctx.stroke();

            // 眨眼时的眼皮线
            if (blink > 0.1) {
                ctx.strokeStyle = c.skinShadow;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(-eyeW, 0);
                ctx.quadraticCurveTo(0, -2 * (1 - blink), eyeW, 0);
                ctx.stroke();
            }

            // 睫毛（上眼线外侧）
            if (blink < 0.5) {
                ctx.strokeStyle = "rgba(30,20,10,0.7)";
                ctx.lineWidth = 1.5;
                for (let i = -2; i <= 2; i++) {
                    const x = i * 6;
                    const y = -Math.sqrt(Math.max(0, eyeH * eyeH - x * x * (eyeH / eyeW) * (eyeH / eyeW)));
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.lineTo(x + side * 2, y - 5);
                    ctx.stroke();
                }
            }

            ctx.restore();
        }
    }

    // ═══ 嘴部 ═══
    drawMouth(ctx) {
        const c = this.colors;
        const mouthY = 65;
        const open = this.mouthOpen;
        const smile = this.smileAmount;
        const halfW = 28 + smile * 5;

        // 嘴部阴影
        ctx.fillStyle = "rgba(0,0,0,0.04)";
        ctx.beginPath();
        ctx.ellipse(0, mouthY + 2, halfW + 2, 4, 0, 0, Math.PI * 2);
        ctx.fill();

        if (open < 0.05) {
            // 闭嘴 - 微笑曲线
            ctx.strokeStyle = c.lipDeep;
            ctx.lineWidth = 4;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(-halfW, mouthY);
            ctx.quadraticCurveTo(0, mouthY + 10 + smile * 8, halfW, mouthY);
            ctx.stroke();

            // 下唇高光
            ctx.fillStyle = c.lipLight;
            ctx.beginPath();
            ctx.ellipse(0, mouthY + 5, halfW * 0.7, 3, 0, 0, Math.PI * 2);
            ctx.fill();
        } else {
            // 张嘴 - 椭圆嘴形
            const mouthH = 8 + open * 20;

            // 口腔
            const mouthGrad = ctx.createRadialGradient(0, mouthY, 2, 0, mouthY + mouthH * 0.3, mouthH);
            mouthGrad.addColorStop(0, "#5a2020");
            mouthGrad.addColorStop(0.6, "#3a1010");
            mouthGrad.addColorStop(1, "#2a0808");
            ctx.fillStyle = mouthGrad;
            ctx.beginPath();
            ctx.ellipse(0, mouthY + mouthH * 0.3, halfW * 0.85, mouthH, 0, 0, Math.PI * 2);
            ctx.fill();

            // 上唇
            ctx.fillStyle = c.lip;
            ctx.beginPath();
            ctx.moveTo(-halfW, mouthY);
            ctx.bezierCurveTo(-halfW * 0.5, mouthY - 4, -3, mouthY - 3, 0, mouthY - 1);
            ctx.bezierCurveTo(3, mouthY - 3, halfW * 0.5, mouthY - 4, halfW, mouthY);
            ctx.bezierCurveTo(halfW * 0.7, mouthY + 2, halfW * 0.3, mouthY + 3, 0, mouthY + 1);
            ctx.bezierCurveTo(-halfW * 0.3, mouthY + 3, -halfW * 0.7, mouthY + 2, -halfW, mouthY);
            ctx.closePath();
            ctx.fill();

            // 下唇
            ctx.fillStyle = c.lip;
            ctx.beginPath();
            ctx.moveTo(-halfW * 0.85, mouthY + mouthH * 0.5);
            ctx.bezierCurveTo(-halfW * 0.5, mouthY + mouthH + 4, halfW * 0.5, mouthY + mouthH + 4, halfW * 0.85, mouthY + mouthH * 0.5);
            ctx.bezierCurveTo(halfW * 0.5, mouthY + mouthH * 0.3, -halfW * 0.5, mouthY + mouthH * 0.3, -halfW * 0.85, mouthY + mouthH * 0.5);
            ctx.closePath();
            ctx.fill();

            // 下唇高光
            ctx.fillStyle = "rgba(255,200,200,0.3)";
            ctx.beginPath();
            ctx.ellipse(0, mouthY + mouthH * 0.7, halfW * 0.4, 2, 0, 0, Math.PI * 2);
            ctx.fill();

            // 牙齿（嘴张开较大时）
            if (open > 0.3) {
                ctx.fillStyle = "#f0ece4";
                ctx.beginPath();
                ctx.ellipse(0, mouthY + 2, halfW * 0.7, 3 + open * 2, 0, 0, Math.PI);
                ctx.fill();
            }
        }
    }

    // ═══ 前方头发 ═══
    drawHairFront(ctx) {
        const c = this.colors;
        const grad = ctx.createLinearGradient(0, -130, 0, -30);
        grad.addColorStop(0, c.hairDark);
        grad.addColorStop(0.5, c.hairMid);
        grad.addColorStop(1, c.hairLight);
        ctx.fillStyle = grad;

        // 刘海
        ctx.beginPath();
        ctx.moveTo(-105, -80);
        ctx.bezierCurveTo(-110, -120, -80, -140, -30, -138);
        ctx.bezierCurveTo(-10, -140, 10, -140, 30, -138);
        ctx.bezierCurveTo(80, -140, 110, -120, 105, -80);
        // 左侧刘海
        ctx.bezierCurveTo(95, -60, 80, -40, 60, -35);
        ctx.bezierCurveTo(50, -45, 40, -55, 25, -50);
        ctx.bezierCurveTo(15, -65, 5, -70, -10, -60);
        ctx.bezierCurveTo(-25, -50, -40, -55, -50, -45);
        ctx.bezierCurveTo(-60, -50, -75, -55, -85, -50);
        ctx.bezierCurveTo(-95, -60, -100, -70, -105, -80);
        ctx.closePath();
        ctx.fill();

        // 头发高光
        ctx.strokeStyle = c.hairHighlight;
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.4;
        ctx.beginPath();
        ctx.moveTo(-60, -100);
        ctx.bezierCurveTo(-40, -125, 20, -130, 60, -110);
        ctx.stroke();
        ctx.globalAlpha = 1;

        // 鬓角
        ctx.fillStyle = c.hairMid;
        ctx.beginPath();
        ctx.moveTo(-100, -70);
        ctx.bezierCurveTo(-105, -40, -102, -10, -95, 10);
        ctx.bezierCurveTo(-92, -10, -90, -40, -88, -70);
        ctx.closePath();
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(100, -70);
        ctx.bezierCurveTo(105, -40, 102, -10, 95, 10);
        ctx.bezierCurveTo(92, -10, 90, -40, 88, -70);
        ctx.closePath();
        ctx.fill();
    }

    destroy() {
        window.removeEventListener("mousemove", this._onMouseMove);
    }
}
