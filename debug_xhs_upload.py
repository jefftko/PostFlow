# -*- coding: utf-8 -*-
"""
调试脚本：检查小红书上传页面的实际 DOM 结构
"""
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import sys

sys.path.insert(0, '.')
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script

ACCOUNT_FILE = Path(BASE_DIR) / 'cookies' / 'xiaohongshu_uploader' / 'account.json'
VIDEO_FILE = '/Volumes/Jeff2TEXTEND1/video/nanhara/2026-02-04/nanhuangshuo-ep08-2026-02-04.mp4'

async def debug():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=str(ACCOUNT_FILE))
        context = await set_init_script(context)
        page = await context.new_page()
        
        print("打开小红书上传页面...")
        await page.goto("https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video")
        await page.wait_for_url("https://creator.xiaohongshu.com/publish/publish?from=homepage&target=video")
        
        print("开始上传视频...")
        await page.locator("div[class^='upload-content'] input[class='upload-input']").set_input_files(VIDEO_FILE)
        
        print("\n等待30秒让视频上传...")
        print("观察页面并检查 DOM...")
        
        for i in range(30):
            await asyncio.sleep(2)
            print(f"\n=== 检查 #{i+1} ===")
            
            # 检查各种可能的上传成功标识
            checks = [
                ('div.stage:has-text("上传成功")', '上传成功 stage'),
                ('div:has-text("上传成功")', '任意上传成功'),
                ('div.preview-new', 'preview-new'),
                ('div[class*="upload-success"]', 'upload-success class'),
                ('div[class*="success"]', 'success class'),
                ('video', 'video 标签'),
                ('div:has-text("重新上传")', '重新上传按钮'),
            ]
            
            for selector, name in checks:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"  ✓ {name}: {count} 个")
                except:
                    pass
            
            # 获取 upload-input 附近的 HTML
            try:
                upload_area = await page.query_selector('input.upload-input')
                if upload_area:
                    parent = await upload_area.evaluate_handle('el => el.parentElement')
                    html = await parent.evaluate('el => el.innerHTML.substring(0, 500)')
                    print(f"  上传区域 HTML 片段: {html[:200]}...")
            except Exception as e:
                print(f"  获取 HTML 失败: {e}")
        
        print("\n按 Enter 关闭浏览器...")
        input()
        await browser.close()

if __name__ == '__main__':
    asyncio.run(debug())
