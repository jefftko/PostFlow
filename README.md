# PostFlow 📤

**PostFlow** 是一个多平台内容自动发布工具，帮助内容创作者一键发布视频、文章到多个社交媒体平台。

> 🔀 本项目 fork 自 [dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload)，感谢原作者的开源贡献！

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

## 🔧 本地改动

相比原项目，本 fork 增加了：

- **description 参数**：支持填写视频描述
- **标题定位修复**：使用 placeholder 精确定位
- **定时发布修复**：使用 `fill()` 替换整个值，确保日期时间正确

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

基于 [dreammis/social-auto-upload](https://github.com/dreammis/social-auto-upload) 开发。

---

Made with ❤️ by [jefftko](https://github.com/jefftko)
