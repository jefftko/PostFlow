# PostFlow 📤

**PostFlow** 是一个多平台内容自动发布工具，帮助内容创作者一键发布视频、文章到多个社交媒体平台。

---

## 🤖 AI agent / 新人 — 第一步读这里（按顺序）

如果你是被指派来配置或使用这个项目的 **AI agent**（Claude / GPT / Cursor / Cline 等），**不要直接跑 `pip install -r requirements.txt`**——按下面顺序读 + 跑，能避免装 1 小时还失败：

| 操作系统 | 第一步读 | 第二步读 |
|---|---|---|
| **Windows** | 📘 [`docs/INSTALL_WINDOWS.md`](docs/INSTALL_WINDOWS.md) | 📕 [`docs/PUBLISH_GUIDE.md`](docs/PUBLISH_GUIDE.md) |
| **macOS / Linux** | 📕 [`docs/PUBLISH_GUIDE.md`](docs/PUBLISH_GUIDE.md) §1 安装 | 📕 同一篇 §3-5 抖音/小红书上传 |

**关键约束**（避免常见错误）：
1. ✅ 用 **Python 3.11**（不要用 3.13，cp313 wheel 不全）
2. ✅ 装依赖用 **`requirements-minimal.txt`**（`requirements.txt` 把 cffi 等 pin 死了，Windows 会撞 MSVC Build Tools 墙）
3. ✅ 先 `pip install --upgrade pip setuptools wheel` 再装依赖
4. ✅ `conf.py` 里 `LOCAL_CHROME_PATH` 指本机已装 Chrome（不要用 Playwright bundled chromium，会被风控）
5. ❌ 不要把 `cookies/` / `account.json` / `token.pickle` 提交到任何仓库

如果你跑了 1 小时还没装上 —— **大概率漏了第 1 或第 2 条**，回去重读 INSTALL 文档。

---

## ✨ 功能特性

### 已支持平台

**视频平台：**
- [x] 抖音
- [x] 视频号
- [x] Bilibili
- [x] 小红书
- [x] 快手
- [x] 百家号
- [x] TikTok

**计划支持：**
- [ ] 微信公众号（文章）
- [ ] 字节头条
- [ ] YouTube

### 核心功能

- [x] 多平台视频上传
- [x] 定时发布
- [x] 标题、描述、标签自动填充
- [x] Cookie 管理
- [ ] 公众号图文发布
- [ ] 统一内容管理后台

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/jefftko/PostFlow.git
cd PostFlow
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 获取 Cookie（以抖音为例）

```bash
python examples/get_douyin_cookie.py
# 扫码登录后自动保存 cookie
```

### 上传视频

```python
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from datetime import datetime

# 配置
video = DouYinVideo(
    title="视频标题",
    file_path="/path/to/video.mp4",
    tags=["标签1", "标签2"],
    publish_date=datetime(2026, 2, 5, 19, 0),  # 定时发布
    account_file="cookies/douyin_uploader/account.json",
    description="视频描述内容",
)

# 上传
import asyncio
asyncio.run(video.main())
```

## 📁 项目结构

```
PostFlow/
├── uploader/           # 各平台上传器
│   ├── douyin_uploader/
│   ├── tencent_uploader/
│   ├── bilibili_uploader/
│   └── ...
├── examples/           # 示例脚本
├── cookies/            # Cookie 存储
└── conf.py            # 配置文件
```

## 🔧 已修复 / 增强

- **抖音**：JS click 绕过 canvas / 多 selector fallback / 本地 Chrome
- **小红书**：★ Web Component 发布按钮 selector / 定时逻辑重写
- **视频号**：`wait_for_selector` 替代固定 sleep / `.first` 防 strict mode
- **视频 description 参数**：支持填写完整描述
- **标题定位修复**：使用 placeholder 精确定位
- **定时发布修复**：使用 `fill()` 替换整个值，确保日期时间正确

详见 [`docs/PUBLISH_GUIDE.md`](docs/PUBLISH_GUIDE.md) 「已知坑 + 解法」一节。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

基于 [dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload) 开发。

---

Made with ❤️ by [jefftko](https://github.com/jefftko)
