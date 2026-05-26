# Windows 安装指南（避坑版）

> Windows 安装本项目常见卡点：cffi 源码编译要 Microsoft C++ Build Tools / requirements.txt 编码错乱 / Playwright 浏览器路径 / PowerShell UTF-8。
>
> **本文档给一条按顺序照跑的命令**，跑完即可。如果你按 [`PUBLISH_GUIDE.md`](PUBLISH_GUIDE.md) 通用教程在 Windows 卡住，回来读这一篇。

---

## TL;DR · 最稳的 5 条命令（Windows 11 / Python 3.11）

打开 **PowerShell**（不是 cmd），按顺序执行：

```powershell
# 1. clone
cd D:\Work
git clone https://github.com/jefftko/PostFlow.git
cd PostFlow

# 2. Python 3.11 虚拟环境（★ 不要用 3.13，cffi/lxml wheel 不全）
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1

# 3. ★ 升级 pip 到最新（旧 pip 找 wheel 能力差，会强制源码编译）
python -m pip install --upgrade pip setuptools wheel

# 4. ★ 用 minimal 依赖（避开过度 pin 死的版本）
pip install -r requirements-minimal.txt

# 5. Playwright 浏览器
playwright install chromium
```

跑完，去 [`PUBLISH_GUIDE.md`](PUBLISH_GUIDE.md) 走登录 + 上传流程。

---

## 为什么 Windows 装 `requirements.txt` 会失败

### 问题 1：`cffi==1.17.1` 走源码编译，需要 Microsoft C++ Build Tools

**症状**：
```
error: Microsoft Visual C++ 14.0 or greater is required.
Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**根因**：
- `requirements.txt` 把 cffi 锁到 `==1.17.1`
- cffi 1.17.1 在 Python 3.13 上**没有预编译 wheel**（只有 3.10-3.12 的 wheel）
- pip 找不到 wheel → 回退到源码编译 → 调用 MSVC → 你没装 Build Tools → 失败

**解法**（任选一）：
1. **降 Python 到 3.11**（推荐）—— cffi 1.17.1 有 cp311 wheel，免编译
2. **用 `requirements-minimal.txt`**（推荐）—— 用 `cffi>=1.17` 不 pin 死，pip 会拿到 3.13 的最新 wheel
3. **装 Microsoft C++ Build Tools**（不推荐，下载 5GB+）：https://visualstudio.microsoft.com/visual-cpp-build-tools/ → Build Tools → C++ build tools 工作负载

### 问题 2：requirements.txt 编码错乱（已修复，但 fork 自旧版的请注意）

如果你 fork 自 PostFlow 2026-05-26 之前的版本，`requirements.txt` 可能是 UTF-16 BOM + CRLF，PowerShell `Out-File` 默认就这样输出的，pip 解析会乱。

**症状**：
```
ERROR: Could not parse package requirement: '\xff\xfeaiofiles'
```

**解法**：拉最新 main 分支（已修复为 UTF-8 LF）；或本地转码：
```powershell
Get-Content requirements.txt -Encoding Unicode | Set-Content requirements.txt -Encoding UTF8
```

### 问题 3：lxml / cryptography / pillow 也可能要编译

同样的根因：版本 pin 太死 → wheel 不匹配 → 源码编译。`requirements-minimal.txt` 用宽松约束规避。

### 问题 4：PowerShell 默认 GBK 编码看 README 乱码

**症状**：`cat README.md` 中文乱码。

**解法**：PowerShell 设 UTF-8：
```powershell
chcp 65001
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

或者用 VS Code / Notepad++ 打开 .md 文件（自动识别 UTF-8）。

### 问题 5：Playwright Chromium 路径

Playwright 在 Windows 上把 Chromium 装到 `%USERPROFILE%\AppData\Local\ms-playwright\chromium-*\`，**这个路径有空格、有 AppData**，部分脚本路径处理不当会失败。

**解法**：在 `conf.py` 设 **本机已装的 Chrome**（推荐）：
```python
LOCAL_CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LOCAL_CHROME_HEADLESS = False  # 首次跑先看着，确认每一步正确
```

> `r""` 前缀很关键——Windows 路径反斜杠不加 raw 会被 Python 解析成转义符。

---

## 完整 Windows 安装流程（详细版）

### 0. 准备

- Windows 10/11
- **Python 3.11**（强烈推荐）：https://www.python.org/downloads/release/python-3119/ → 选 "Windows installer (64-bit)"
  - ⚠️ 安装时**勾选 "Add Python to PATH"**
  - ⚠️ 不要用 Python 3.13——很多包还没 cp313 wheel
- Git for Windows：https://git-scm.com/download/win
- **Google Chrome 已安装**（任何最新版即可）

### 1. 克隆仓库

```powershell
# 选一个不含中文、不含空格的目录
cd D:\Work
git clone https://github.com/jefftko/PostFlow.git
cd PostFlow
```

### 2. 创建虚拟环境

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

⚠️ 如果 PowerShell 报「无法加载文件 Activate.ps1，因为在此系统上禁止运行脚本」：
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
确认后重新跑 `Activate.ps1`。

### 3. 升级 pip / setuptools / wheel

```powershell
python -m pip install --upgrade pip setuptools wheel
```

⚠️ **这一步不能跳过**——旧版 pip 找 wheel 的能力差，会让你装 1 小时还失败。

### 4. 安装依赖

**首选**（最稳）：
```powershell
pip install -r requirements-minimal.txt
```

**备选**（如果你需要 web 后端 / 完整依赖）：
```powershell
pip install -r requirements.txt
```

如果 `requirements.txt` 装失败：
1. 看错误最后一行——是哪个包要编译？
2. 单独装这个包的最新版（不 pin 死）：`pip install cffi` / `pip install lxml`
3. 再回头跑 `pip install -r requirements.txt`，已装过的会跳过

### 5. Playwright 浏览器（仅 chromium）

```powershell
playwright install chromium
```

下载约 150MB，需要 3-5 分钟。装完位置：`%USERPROFILE%\AppData\Local\ms-playwright\chromium-*`

### 6. 配置 conf.py

```powershell
copy conf.example.py conf.py
notepad conf.py
```

编辑 conf.py，至少改两行：
```python
BASE_DIR = r"D:\Work\PostFlow"
LOCAL_CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LOCAL_CHROME_HEADLESS = False  # 首次跑保留 False
```

### 7. 验证 — 跑一次抖音登录

```powershell
python examples\get_douyin_cookie.py
```

应该弹出 Chrome → 加载抖音创作者中心 → 你用手机抖音扫码 → 保存 `cookies\douyin_uploader\account.json`。

成功后回到 [`PUBLISH_GUIDE.md`](PUBLISH_GUIDE.md) 第 3 节看怎么上传视频。

---

## 已知 Windows 特定坑

### 坑 1：路径分隔符 `/` vs `\`

Python 写跨平台代码用 `pathlib.Path`：
```python
from pathlib import Path
account_file = Path("cookies") / "douyin_uploader" / "account.json"  # ✅ 跨平台
account_file = "cookies/douyin_uploader/account.json"  # ⚠️ Windows 上有时会被某些库拒
account_file = "cookies\\douyin_uploader\\account.json"  # ❌ 不可移植
```

仓库代码已经用 `Path`，不用改。但你**自己包装脚本时**注意。

### 坑 2：文件名含中文 / 空格

抖音/小红书后台的 web 上传不识别某些非 ASCII 文件名。**保险写法**：
- 视频文件名只用英文+数字+下划线：`video-2026-05-26.mp4` ✅
- 不要用 `视频.mp4` 这种 ❌

### 坑 3：杀毒软件 / Windows Defender

部分 Windows Defender / 360 / 火绒会拦 Playwright 的 chromium，弹窗"病毒/木马"。
- 解法：把 `%USERPROFILE%\AppData\Local\ms-playwright\` 加白名单
- 或者把整个 PostFlow 项目目录加白名单

### 坑 4：Chrome 已经开着 → Playwright 启动失败

如果你的 Chrome 在用同一个 profile，Playwright 用 `executable_path` 启动新实例时会拒绝（"Chrome is already running"）。

**解法**：跑脚本前**关掉所有 Chrome 窗口**；或者改用 Edge：
```python
LOCAL_CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

### 坑 5：定时发布时区

抖音/小红书后台显示 BJT（北京时间）。如果你的 Windows 系统时区不是 BJT：
```python
from datetime import datetime, timedelta, timezone
publish_date = datetime.now(timezone(timedelta(hours=8))) + timedelta(hours=2)
```

或直接系统设 BJT。

---

## 如果还是失败 — 给一个最小可复现的报错

去仓库提 Issue：https://github.com/jefftko/PostFlow/issues/new

提供：
1. Windows 版本（Win 10/11）
2. Python 版本（`python --version`）
3. pip 版本（`pip --version`）
4. 完整错误堆栈最后 30 行
5. 跑的是 `requirements.txt` 还是 `requirements-minimal.txt`

不要只说"装不了"——那等于没说。
