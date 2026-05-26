# 抖音 / 小红书 自动上传 · 实战手册

> 给任何想用本项目把视频自动发布到抖音、小红书的人（包括 AI agent）的一份**可直接复制照跑**的实战指南。
>
> 覆盖：**安装 → 登录拿 cookie → Python 调用上传 → 定时发布 → 已知坑 + 解法**。

---

## 0. 设计核心（30 秒理解整套机制）

本工具用 **Playwright 浏览器自动化**驱动抖音 / 小红书的 web 创作者后台，**不调任何官方 API**（官方上传 API 个人开发者拿不到）。

整套流程只有两步：

1. **首次扫码登录** → 把浏览器登录态序列化为 `account.json` 文件
2. **每次上传** → Playwright 加载这个 `account.json` 还原登录态 → 模拟点击「上传 → 填标题 → 加标签 → 定时 → 发布」

> 因为本质是浏览器自动化，所以**任何 web 端 UI 改版都可能破坏脚本**。本仓库的 `uploader/douyin_uploader/main.py` 和 `uploader/xiaohongshu_uploader/main.py` 已经针对 2026-Q1 / Q2 的多次 UI 改版做了修复（详见「已知坑」一节）。

---

## 1. 安装

> ⚠️ **Windows 用户请先看 [`docs/INSTALL_WINDOWS.md`](INSTALL_WINDOWS.md)** —— Windows 有特定坑（cffi 源码编译 / 编码 / PowerShell），按那篇照跑能避免装 1 小时还失败。
>
> macOS / Linux 跟下面通用步骤即可。

```bash
# 1. clone
git clone https://github.com/jefftko/PostFlow.git
cd PostFlow

# 2. Python 3.10/3.11/3.12（推荐 3.11），创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate              # macOS/Linux
# .\venv\Scripts\Activate.ps1         # Windows PowerShell

# 3. ★ 升级 pip 再装依赖（否则旧 pip 找 wheel 能力差，可能强制源码编译）
python -m pip install --upgrade pip setuptools wheel

# 4. 装依赖（首选 minimal 版本约束宽松，跨平台更稳）
pip install -r requirements-minimal.txt
# 完整版（含 Flask web 后端）：pip install -r requirements.txt

# 5. Playwright 浏览器（chromium 即可）
playwright install chromium

# 6. 拷贝配置
cp conf.example.py conf.py
# 编辑 conf.py 改两行：
#   BASE_DIR        = "/your/abs/path/to/PostFlow"
#   LOCAL_CHROME_PATH = "/Applications/Google Chrome.app/.../Google Chrome"  # 留空跑 playwright bundled chromium

# 7. （可选）初始化数据库
python db/createTable.py
```

### Chrome 路径（`LOCAL_CHROME_PATH`）

抖音 / 小红书后台对 chromium 检测严格，**推荐用本机已装的 Chrome / Edge** 而不是 Playwright bundled chromium，登录稳定性高很多。

| 平台 | 默认路径 |
|---|---|
| macOS | `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` |
| Linux | `/usr/bin/google-chrome` |
| Windows | `C:\Program Files\Google\Chrome\Application\chrome.exe` |

**留空** = 用 Playwright bundled chromium（容易被风控）。

---

## 2. 目录结构（关键文件位置）

```
PostFlow/
├── uploader/
│   ├── douyin_uploader/main.py       ← 抖音核心 ★
│   ├── xiaohongshu_uploader/main.py  ← 小红书核心 ★（新版，请用这个）
│   ├── xhs_uploader/                  ← 小红书旧版（仅保留 sign_local 签名工具，不要用 main.py 上传）
│   ├── tencent_uploader/main.py      ← 视频号
│   ├── bilibili_uploader/             ← B 站
│   ├── ks_uploader/                   ← 快手
│   ├── tk_uploader/                   ← TikTok
│   └── baijiahao_uploader/            ← 百家号
├── examples/
│   ├── upload_video_to_douyin.py     ← 抖音上传示例 ★
│   ├── upload_video_to_xiaohongshu.py ← 小红书上传示例 ★
│   ├── get_douyin_cookie.py          ← 抖音扫码登录 ★
│   └── get_xiaohongshu_cookie.py     ← 小红书扫码登录 ★
├── cookies/                            ← 各平台 cookie 存放（运行时生成，不入仓）
├── conf.py                             ← 配置（不入仓）
└── docs/PUBLISH_GUIDE.md               ← 本手册
```

> **⚠️ 双小红书目录混淆**：
> - `uploader/xiaohongshu_uploader/` = **新版核心，主用**（含 Web Component 修复）
> - `uploader/xhs_uploader/` = 旧版，**只保留 `sign_local` 签名工具**给 `myUtils/auth.py` 用，**不要拿它的 main.py 上传**

---

## 3. 抖音上传

### 3.1 首次登录拿 cookie（扫码一次，长期有效）

```bash
cd PostFlow
source venv/bin/activate
python examples/get_douyin_cookie.py
```

执行后：
1. 弹出 Chrome 浏览器到「抖音创作者中心登录页」
2. **手机抖音 APP 扫码登录**
3. 登录成功后脚本自动保存登录态到：`cookies/douyin_uploader/account.json`
4. 关闭浏览器，脚本退出

> ✅ 这个 `account.json` 包含 cookie + localStorage + sessionStorage，下次上传直接加载，**不用再扫码**。
>
> ⚠️ 抖音 cookie 实测**有效期约 1-2 周**，过期会报「cookie 失效」，重跑这个脚本扫一次码即可。

### 3.2 上传一个视频（最小可跑代码）

```python
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo

async def main():
    account_file = Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json"
    video_file = Path("/abs/path/to/your-video.mp4")
    
    # Step 1: 验证 cookie 有效性（无效会自动打开浏览器要求重新登录）
    await douyin_setup(account_file, handle=False)
    
    # Step 2: 构造上传任务
    app = DouYinVideo(
        title="你的视频标题（≤30 字推荐）",
        file_path=video_file,
        tags=["标签1", "标签2", "标签3"],  # 抖音标签
        publish_date=datetime.now() + timedelta(hours=2),  # 定时 2 小时后发布
        account_file=account_file,
        thumbnail_path=None,         # 可选：自定义封面图路径
        description="完整文案/描述（可选）"
    )
    
    # Step 3: 执行
    await app.main()

asyncio.run(main())
```

### 3.3 立即发布 vs 定时发布

| 模式 | publish_date 传什么 |
|---|---|
| **立即发布** | `datetime.now()`（或当前时间 + 几分钟） |
| **定时发布** | 未来时间，如 `datetime(2026, 5, 26, 20, 0)` |

抖音定时发布限制：**只能定 2 小时后到 14 天内**。

### 3.4 多账号

每个账号一个独立 `account.json`：

```
cookies/
├── douyin_uploader/
│   ├── account_a.json    ← 账号 A
│   ├── account_b.json    ← 账号 B
│   └── account_c.json    ← 账号 C
```

调用时传不同 `account_file` 即可。**多账号一定要分 cookie 目录，不要共用**——抖音会检测异常登录。

---

## 4. 小红书上传

### 4.1 首次登录拿 cookie

```bash
python examples/get_xiaohongshu_cookie.py
```

流程同抖音：弹出 Chrome → 小红书 APP 扫码 → 保存到 `cookies/xiaohongshu_uploader/account.json`。

> ⚠️ 小红书 cookie 有效期**比抖音短**，约 1 周。过期重扫即可。

### 4.2 上传一个视频

```python
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from conf import BASE_DIR
from uploader.xiaohongshu_uploader.main import xiaohongshu_setup, XiaoHongShuVideo

async def main():
    account_file = Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json"
    video_file = Path("/abs/path/to/your-video.mp4")
    
    await xiaohongshu_setup(account_file, handle=False)
    
    app = XiaoHongShuVideo(
        title="标题（≤20 字推荐）",
        file_path=video_file,
        tags=["#标签1", "#标签2"],       # 小红书标签建议带 # 前缀
        publish_date=datetime.now() + timedelta(hours=2),
        account_file=account_file,
        thumbnail_path=None,           # 可选
        description="正文/笔记内容"
    )
    
    await app.main()

asyncio.run(main())
```

### 4.3 小红书 vs 抖音 参数差异

| 项 | 抖音 | 小红书 |
|---|---|---|
| 类 | `DouYinVideo` | `XiaoHongShuVideo` |
| 标题字数 | ≤30 | ≤20 |
| 标签格式 | `["标签"]` | `["#标签"]` |
| 字段 | description = 文案 | description = 正文/笔记 |
| 平台特有字段 | productLink / productTitle（橱窗）| — |

---

## 5. ⚠️ 已知坑 + 解法（实战踩坑沉淀）

### 5.1 抖音「定时发布」按钮点不到 — JS 点击绕过 canvas

**症状**：playwright 的 `.click()` 报「element is outside of the viewport / blocked by canvas」。

**根因**：抖音创作者中心的「定时发布」单选按钮被一个 canvas 覆盖层挡住。

**解法**（已在 `douyin_uploader/main.py` 实现）：
```python
# 用 evaluate 直接 JS 点击，绕过 canvas
await label_element.first.evaluate("el => el.click()")
```

### 5.2 抖音定时时间输入框 selector 飘 — 多 selector fallback

**症状**：今天能点到，明天就找不到。

**根因**：抖音 web 后台用了不同 class 名（`.semi-input` / `.semi-datepicker-input` / `input[placeholder="日期和时间"]`），偶尔切换。

**解法**（已实现）：按优先级试多个 selector，找到就用：
```python
selectors = [
    '.semi-input[placeholder="日期和时间"]',
    'input[placeholder="日期和时间"]',
    '.semi-datepicker-input input',
    'input.semi-input[type="text"]',
]
```

### 5.3 ★ 小红书「定时发布」按钮是 Web Component，所有 `has-text` selector 永远匹配不到

**症状**：脚本能填完所有字段，但最后那个红色「定时发布」按钮就是点不到。`page.locator('button:has-text("定时发布")')` 返回 0。

**根因**：小红书的发布按钮**不是 `<button>`**，是一个**自定义 web component**：
```html
<xhs-publish-btn submit-text="定时发布" submit-disabled="false">
```

任何针对 `<button>` 标签 + `has-text` 的 selector 都失败。

**解法**（已在 `xiaohongshu_uploader/main.py` 实现）：直接用 web component 的 tag name + 属性 selector：
```python
btn = page.locator('xhs-publish-btn[submit-text="定时发布"][submit-disabled="false"]')
await btn.click()
```

> 这是踩坑 5+ 次后才定位到的根因。任何 fork 都应该 cherry-pick 这段修复。

### 5.4 抖音 / 小红书工作台「失败草稿」污染 selector

**症状**：上传几次后，脚本开始狂报「找不到上传入口 / 找不到发布按钮」，但手动登进去看其实正常。

**根因**：之前失败的上传会在工作台留下「草稿/失败」记录，这些记录里也有「发布」「定时」等同名按钮，会被脚本的 selector **错误匹配到**（比如 `div.status-msg.error`）。

**解法**：
1. **每次上传前手动登录工作台清理失败草稿**（最稳）
2. 脚本里加重试上限（已加 5 次，避免无限循环）
3. **上传期间绝不要在另一个浏览器里打开同账号的工作台 rotate cookie**——会触发「登录态异常」中断

### 5.5 cookie 过期了 — 怎么续

```bash
# 重跑登录脚本即可，会覆盖旧 account.json
python examples/get_douyin_cookie.py       # 抖音
python examples/get_xiaohongshu_cookie.py  # 小红书
```

> ⚠️ **多账号场景**：登录脚本默认覆盖 `cookies/<platform>_uploader/account.json`，多账号要手动改路径（或拷贝示例脚本改成你的）。

### 5.6 Playwright 检测被反爬 — 用本机 Chrome 而非 bundled chromium

**症状**：登录页直接卡死 / 滑块验证永远过不去。

**解法**：在 `conf.py` 设 `LOCAL_CHROME_PATH` 为本机已装的 Chrome 路径（见 [安装](#1-安装) 一节）。bundled chromium 风控触发率高。

### 5.7 标题被截断 / 标签变成纯文本

**抖音**：
- 标题最多 30 字（含空格），超出会被截断
- 标签传 `["tag1", "tag2"]` 即可，**不要带 `#`**——脚本会自动加

**小红书**：
- 标题最多 20 字
- 标签**必须带 `#`**：`["#标签1", "#标签2"]`
- 标签会出现在正文末尾（不是单独标签栏）

### 5.8 视频文件格式

抖音/小红书 web 端都支持 mp4，但有要求：
- **抖音**：H.264 编码 / 1080p 推荐 / ≤4 GB / 时长 ≤ 15 分钟（创作者中心）
- **小红书**：H.264 / 720p+ / ≤4 GB / 时长 ≤ 15 分钟
- ❌ 不支持 HEVC/H.265（部分浏览器解析失败）

转码命令（保险写法）：
```bash
ffmpeg -i input.mp4 -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 128k output.mp4
```

---

## 6. 调试 / 排错

### 6.1 看着浏览器跑（关 headless）

`conf.py` 里把 `LOCAL_CHROME_HEADLESS = False` —— 上传时浏览器会显示出来，能直接看到卡在哪一步。

### 6.2 看日志

```bash
tail -f logs/douyin_*.log
tail -f logs/xiaohongshu_*.log
```

每个平台独立 logger。如果脚本卡住，**日志里最后一行就是卡住的步骤**。

### 6.3 手动 reproduce 问题

把 `account_file` 加载到浏览器：
```python
import asyncio
from playwright.async_api import async_playwright
from conf import LOCAL_CHROME_PATH

async def open():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, executable_path=LOCAL_CHROME_PATH)
        ctx = await browser.new_context(storage_state="cookies/douyin_uploader/account.json")
        page = await ctx.new_page()
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        await asyncio.sleep(3600)  # 浏览器开着不关，你手动点

asyncio.run(open())
```

可以直接看抖音 / 小红书后台当前的 UI 长什么样、对比 selector 是否还能命中。

---

## 7. CLI 用法（不写 Python 也能跑）

仓库根目录 `cli_main.py` 提供命令行：

```bash
# 登录
python cli_main.py login --platform douyin
python cli_main.py login --platform xiaohongshu

# 上传
python cli_main.py upload \
    --platform douyin \
    --file /abs/path/to/video.mp4 \
    --title "标题" \
    --tags "标签1,标签2" \
    --account cookies/douyin_uploader/account.json

# 定时
python cli_main.py upload \
    --platform xiaohongshu \
    --file /abs/path/to/video.mp4 \
    --title "标题" \
    --tags "#标签1,#标签2" \
    --schedule "2026-05-26 20:00" \
    --account cookies/xiaohongshu_uploader/account.json
```

---

## 8. 一些建议（避免常见错误）

1. **首次跑前 headless = False**——看着浏览器跑一次，确认每一步都对，再切 True
2. **多账号严格分 cookie 目录**——别想着省事用一个 account.json 跑多平台
3. **每周清一次工作台失败草稿**——避免 selector 污染
4. **不要在脚本上传期间手动操作同账号**——会触发「登录态异常」
5. **cookie 失败先重扫码再说**——不要花时间 debug 是不是 selector 改了
6. **上传频率别太密**——同账号 24 小时内 ≤ 5 次推荐，超过容易被风控

---

## 9. 不要做

- ❌ 不要把 `cookies/`、`account.json`、`token.pickle` 上传到任何公开仓库
- ❌ 不要把多个账号的 cookie 放在同一个目录
- ❌ 不要用 bundled chromium 跑生产（被风控率高）
- ❌ 不要用 `xhs_uploader/main.py` 上传（旧版，没修 Web Component 坑——用 `xiaohongshu_uploader/main.py`）
- ❌ 不要在脚本里硬编码 cookie 路径——用 `conf.BASE_DIR` 相对路径

---

## 10. 贡献 / 反馈

- 抖音 / 小红书 web 后台改版了 selector 失效？提 issue + PR
- 想加新平台？参考 `uploader/<platform>_uploader/main.py` 的结构（`<platform>_setup` + `<Platform>Video` class）
- 本手册有遗漏？欢迎 PR

---

> 本手册基于 2026-Q2 抖音/小红书 web 后台 UI 编写。如果你看到「现在的 UI 跟手册描述不一样」，先检查 selector 是否还能匹配，参考 [6.3 手动 reproduce](#63-手动-reproduce-问题) 调试。
