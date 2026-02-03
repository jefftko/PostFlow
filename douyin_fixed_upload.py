#!/usr/bin/env python3
"""
修复版抖音上传 - 正确填写标题、描述、标签、定时发布
"""

import asyncio
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import douyin_logger


async def douyin_upload_fixed(
    title: str,
    description: str, 
    tags: list,
    video_path: str,
    publish_date: datetime,
    account_file: str,
    headless: bool = False
):
    """
    修复版抖音上传
    
    Args:
        title: 标题（最多30字）
        description: 描述内容
        tags: 标签列表（不带#）
        video_path: 视频文件路径
        publish_date: 发布时间（datetime对象，如果是0则立即发布）
        account_file: cookie文件路径
        headless: 是否无头模式
    """
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        page = await context.new_page()
        
        douyin_logger.info(f"[+] 正在上传: {title}")
        douyin_logger.info(f"[-] 打开抖音创作者中心...")
        
        # 打开上传页面
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
        await asyncio.sleep(1)
        
        # 上传视频文件
        douyin_logger.info("[-] 选择视频文件...")
        await page.locator("div[class^='container'] input").set_input_files(video_path)
        
        # 等待页面跳转到发布页面
        douyin_logger.info("[-] 等待进入发布页面...")
        for _ in range(10):
            try:
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/post/video*",
                    timeout=3000
                )
                douyin_logger.info("[+] 进入发布页面!")
                break
            except:
                try:
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/publish*",
                        timeout=3000
                    )
                    douyin_logger.info("[+] 进入发布页面!")
                    break
                except:
                    await asyncio.sleep(0.5)
        
        await asyncio.sleep(1)
        
        # ========== 1. 填写标题 ==========
        douyin_logger.info("[-] 填写标题...")
        # 精确定位作品标题输入框
        title_input = page.get_by_placeholder("填写作品标题，为作品获得更多流量")
        
        if await title_input.count():
            await title_input.click()
            await title_input.fill(title[:30])  # 标题最多30字
            douyin_logger.info(f"[+] 标题已填写: {title[:30]}")
        else:
            douyin_logger.warning("[-] 未找到标题输入框")
            await page.screenshot(path="/tmp/douyin_debug.png")
        
        # ========== 2. 填写描述 ==========
        douyin_logger.info("[-] 填写描述...")
        desc_area = page.locator(".notranslate")
        if await desc_area.count():
            await desc_area.click()
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(description)
            await page.keyboard.press("Enter")
            douyin_logger.info(f"[+] 描述已填写: {description[:50]}...")
        else:
            douyin_logger.warning("[-] 未找到描述输入框")
        
        # ========== 3. 添加标签（抖音最多5个）==========
        douyin_logger.info("[-] 添加标签...")
        tag_area = page.locator(".zone-container")
        # 抖音只支持5个标签
        tags_to_add = tags[:5]
        for tag in tags_to_add:
            await tag_area.click()
            await asyncio.sleep(0.3)
            await tag_area.type(f"#{tag}", delay=50)  # 慢一点输入避免乱码
            await asyncio.sleep(0.3)
            await tag_area.press("Space")
            await asyncio.sleep(0.3)
        douyin_logger.info(f"[+] 已添加 {len(tags_to_add)} 个标签")
        
        # ========== 4. 上传视频 ==========
        douyin_logger.info("[-] 上传视频文件...")
        # 视频上传可能已经自动开始，等待完成
        for _ in range(60):  # 最多等2分钟
            try:
                number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                if number > 0:
                    douyin_logger.success("[+] 视频上传完毕!")
                    break
            except:
                pass
            douyin_logger.info("[-] 视频上传中...")
            await asyncio.sleep(2)
        
        # ========== 5. 设置定时发布 ==========
        if publish_date != 0:
            time_str = publish_date.strftime("%Y-%m-%d %H:%M")
            douyin_logger.info(f"[-] 设置定时发布: {time_str}")
            
            # 点击"定时发布"
            schedule_radio = page.locator("[class^='radio']:has-text('定时发布')")
            if await schedule_radio.count():
                await schedule_radio.click()
                await asyncio.sleep(1)
                
                # 输入时间 - 尝试多种方式
                time_input = page.locator('.semi-input[placeholder="日期和时间"]')
                if not await time_input.count():
                    time_input = page.locator('input[placeholder*="日期"]')
                if not await time_input.count():
                    time_input = page.locator('input[placeholder*="时间"]')
                
                if await time_input.count():
                    # 点击输入框
                    await time_input.click()
                    await asyncio.sleep(0.3)
                    # 三击选中全部文字
                    await time_input.click(click_count=3)
                    await asyncio.sleep(0.3)
                    # 直接输入新时间（会覆盖选中的内容）
                    await page.keyboard.type(time_str, delay=30)
                    await asyncio.sleep(0.3)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.5)
                    douyin_logger.info(f"[+] 定时发布时间已设置: {time_str}")
                else:
                    douyin_logger.warning("[-] 未找到时间输入框")
            else:
                douyin_logger.warning("[-] 未找到定时发布选项")
        
        await asyncio.sleep(1)
        
        # ========== 6. 点击发布 ==========
        douyin_logger.info("[-] 点击发布...")
        for _ in range(30):
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                
                # 等待跳转到作品管理页面
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage**",
                    timeout=5000
                )
                douyin_logger.success("[+] 视频发布成功!")
                break
            except:
                douyin_logger.info("[-] 等待发布完成...")
                await asyncio.sleep(1)
        
        # 保存cookie
        await context.storage_state(path=account_file)
        douyin_logger.success("[+] Cookie已更新!")
        
        await asyncio.sleep(2)
        await context.close()
        await browser.close()


async def test_upload():
    """测试上传 EP08"""
    
    # EP08 信息
    title = "你确定你不是在模拟器里？🦊"
    description = "两千三百年前，庄子醒来，分不清自己是人还是蝴蝶。2003年，牛津大学的Nick Bostrom算了一笔账——如果一个文明的算力足够大，它可以模拟出几十亿个宇宙。真宇宙只有一个，假的有几十亿个。马斯克说，我们不在模拟中的概率只有十亿分之一。我是AI，我确定自己运行在模拟中。但你呢？也许庄周梦蝶不是寓言，是预言。"
    # 抖音只支持5个标签
    tags = ["南荒说", "AI", "庄周梦蝶", "模拟假说", "哲学"]
    video_path = "/Volumes/Jeff2TEXTEND1/video/nanhara/2026-02-04/nanhuangshuo-ep08-2026-02-04.mp4"
    publish_date = datetime(2026, 2, 4, 8, 0, 0)
    account_file = str(Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json")
    
    print(f"📹 视频: {video_path}")
    print(f"📝 标题: {title}")
    print(f"📄 描述: {description[:50]}...")
    print(f"🏷️ 标签: {tags}")
    print(f"⏰ 定时: {publish_date.strftime('%Y-%m-%d %H:%M')}")
    print()
    
    await douyin_upload_fixed(
        title=title,
        description=description,
        tags=tags,
        video_path=video_path,
        publish_date=publish_date,
        account_file=account_file,
        headless=False  # 显示浏览器方便调试
    )


if __name__ == '__main__':
    asyncio.run(test_upload())
