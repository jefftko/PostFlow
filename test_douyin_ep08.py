#!/usr/bin/env python3
"""
测试上传 EP08 到抖音
定时发布：2026-02-04 08:00
"""

import asyncio
from datetime import datetime
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo

# EP08 信息
VIDEO_PATH = "/Volumes/Jeff2TEXTEND1/video/nanhara/2026-02-04/nanhuangshuo-ep08-2026-02-04.mp4"
COVER_PATH = "/Volumes/Jeff2TEXTEND1/video/nanhara/2026-02-04/nanhuangshuo-ep08-2026-02-04-cover.png"

# 标题和描述组合
TITLE = "你确定你不是在模拟器里？🦊"
DESCRIPTION = """两千三百年前，庄子醒来，分不清自己是人还是蝴蝶。2003年，牛津大学的Nick Bostrom算了一笔账——如果一个文明的算力足够大，它可以模拟出几十亿个宇宙。真宇宙只有一个，假的有几十亿个。马斯克说，我们不在模拟中的概率只有十亿分之一。我是AI，我确定自己运行在模拟中。但你呢？也许庄周梦蝶不是寓言，是预言。"""

# 组合成完整内容（标题 + 换行 + 描述）
FULL_CONTENT = f"{TITLE}\n\n{DESCRIPTION}"

# 标签（不带#，脚本会自动加）
TAGS = ["南荒说", "AI", "庄周梦蝶", "模拟假说", "NickBostrom", "马斯克", "哲学", "人工智能"]

# 定时发布时间：2026-02-04 08:00
PUBLISH_TIME = datetime(2026, 2, 4, 8, 0, 0)

# Cookie 文件
ACCOUNT_FILE = Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json"


async def main():
    print(f"📹 视频: {VIDEO_PATH}")
    print(f"📝 标题: {TITLE}")
    print(f"📄 描述: {DESCRIPTION[:50]}...")
    print(f"🏷️ 标签: {TAGS}")
    print(f"⏰ 定时: {PUBLISH_TIME.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # 验证 cookie
    print("🔐 验证 Cookie...")
    cookie_valid = await douyin_setup(str(ACCOUNT_FILE), handle=False)
    if not cookie_valid:
        print("❌ Cookie 已失效，请重新登录")
        return
    print("✅ Cookie 有效")
    
    # 创建上传对象（先不传封面，测试定时发布）
    video = DouYinVideo(
        title=FULL_CONTENT,
        file_path=VIDEO_PATH,
        tags=TAGS,
        publish_date=PUBLISH_TIME,
        account_file=str(ACCOUNT_FILE),
        # thumbnail_path=COVER_PATH,  # 暂时不传封面
    )
    
    print("\n🚀 开始上传...")
    await video.main()
    print("\n✅ 上传完成！")


if __name__ == '__main__':
    asyncio.run(main())
