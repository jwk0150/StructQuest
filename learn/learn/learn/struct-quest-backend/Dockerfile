# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖 (Manim 需要 Cairo, LaTeX 等)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango1.0-dev \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    ffmpeg \
    sox \
    latexmk \
    fonts-wqy-zenhei \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Manim (社区版) 用于动画渲染
RUN pip install --no-cache-dir manim>=0.18.0

COPY . .

# 创建视频输出目录
RUN mkdir -p /app/data/videos

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
