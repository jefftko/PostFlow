#!/usr/bin/env python3
"""
南荒说短视频多平台上传脚本

用法:
  python nanhara_upload.py                    # 上传所有未上传的视频(从2/5开始)
  python nanhara_upload.py --date 2026-02-05  # 上传指定日期的视频
  python nanhara_upload.py --dry-run          # 只显示将要上传的内容，不实际上传
"""

import asyncio
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
import argparse

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from uploader.ks_uploader.main import ks_setup, KSVideo
from uploader.tencent_uploader.main import weixin_setup, TencentVideo
from uploader.xiaohongshu_uploader.main import xiaohongshu_setup, XiaoHongShuVideo

# 配置
VIDEO_BASE_DIR = Path("/Volumes/Jeff2TEXTEND1/video/nanhara")
UPLOAD_STATE_FILE = Path(BASE_DIR) / "nanhara_upload_state.json"
MIN_DATE = datetime(2026, 2, 5)  # 只上传2/5及之后的

# 平台配置
PLATFORMS = {
    'douyin': {
        'enabled': True,
        'cookie': Path(BASE_DIR) / "cookies" / "douyin_uploader" / "account.json",
        'setup': douyin_setup,
        'video_class': DouYinVideo,
    },
    'kuaishou': {
        'enabled': False,  # 暂时禁用，有新手引导弹窗问题
        'cookie': Path(BASE_DIR) / "cookies" / "ks_uploader" / "account.json",
        'setup': ks_setup,
        'video_class': KSVideo,
    },
    'tencent': {
        'enabled': True,
        'cookie': Path(BASE_DIR) / "cookies" / "tencent_uploader" / "account.json",
        'setup': weixin_setup,
        'video_class': TencentVideo,
    },
    'xiaohongshu': {
        'enabled': True,
        'cookie': Path(BASE_DIR) / "cookies" / "xiaohongshu_uploader" / "account.json",
        'setup': xiaohongshu_setup,
        'video_class': XiaoHongShuVideo,
    },
}


def load_upload_state():
    """加载上传状态"""
    if UPLOAD_STATE_FILE.exists():
        with open(UPLOAD_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'uploaded': {}}


def save_upload_state(state):
    """保存上传状态"""
    with open(UPLOAD_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def parse_md_file(md_path: Path) -> dict:
    """解析md文件获取标题、描述、标签"""
    content = md_path.read_text(encoding='utf-8')
    
    result = {
        'title': '',
        'description': '',
        'tags': [],
    }
    
    # 提取标题
    title_match = re.search(r'## 标题\n(.+?)(?=\n#|\n\n|$)', content, re.DOTALL)
    if title_match:
        result['title'] = title_match.group(1).strip()
    
    # 提取描述
    desc_match = re.search(r'## 描述\n(.+?)(?=\n#|\n\n##|$)', content, re.DOTALL)
    if desc_match:
        result['description'] = desc_match.group(1).strip()
    
    # 提取标签（带#的）
    tags_match = re.search(r'## 标签（带#）\n(.+?)(?=\n#|\n\n|$)', content, re.DOTALL)
    if tags_match:
        tags_line = tags_match.group(1).strip()
        result['tags'] = [t.strip() for t in tags_line.split() if t.startswith('#')]
    
    return result


def get_publish_datetime(date_str: str, index: int = 0) -> datetime:
    """根据日期字符串生成发布时间，默认当天早上8点"""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    # 第一个视频8点，第二个12点，第三个18点
    hours = [8, 12, 18, 20]
    hour = hours[index % len(hours)]
    return date.replace(hour=hour, minute=0, second=0)


def find_videos_to_upload(target_date: str = None) -> list:
    """查找需要上传的视频"""
    videos = []
    
    for date_dir in sorted(VIDEO_BASE_DIR.iterdir()):
        if not date_dir.is_dir():
            continue
        
        # 检查是否是日期目录
        try:
            dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
        except ValueError:
            continue
        
        # 过滤日期
        if dir_date < MIN_DATE:
            continue
        
        if target_date and date_dir.name != target_date:
            continue
        
        # 查找mp4文件
        for mp4_file in sorted(date_dir.glob('*.mp4')):
            md_file = mp4_file.with_suffix('.md')
            cover_file = mp4_file.with_name(mp4_file.stem + '-cover.png')
            if not cover_file.exists():
                cover_file = mp4_file.with_suffix('.png')
            
            if not md_file.exists():
                print(f"警告: 找不到元数据文件 {md_file}")
                continue
            
            videos.append({
                'date': date_dir.name,
                'video_path': mp4_file,
                'md_path': md_file,
                'cover_path': cover_file if cover_file.exists() else None,
            })
    
    return videos


async def upload_to_platform(platform: str, config: dict, video_info: dict, publish_time: datetime, dry_run: bool = False, schedule: bool = True):
    """上传视频到指定平台"""
    if not config['enabled']:
        return False, "平台已禁用"
    
    if not config['cookie'].exists():
        return False, "Cookie文件不存在"
    
    # 解析元数据
    metadata = parse_md_file(video_info['md_path'])
    
    # 组合标题和描述
    title = metadata['title']
    tags = metadata['tags']
    
    print(f"\n📤 上传到 {platform}:")
    print(f"   视频: {video_info['video_path'].name}")
    print(f"   标题: {title}")
    print(f"   标签: {' '.join(tags)}")
    print(f"   定时: {publish_time.strftime('%Y-%m-%d %H:%M')}")
    
    if dry_run:
        print(f"   [DRY RUN] 跳过实际上传")
        return True, "dry run"
    
    try:
        # 验证cookie
        cookie_valid = await config['setup'](str(config['cookie']), handle=False)
        if not cookie_valid:
            return False, "Cookie已失效"
        
        # 创建视频对象并上传
        # 如果不定时发布，publish_date 设为 0
        actual_publish_time = publish_time if schedule else 0
        video = config['video_class'](
            title=title,
            file_path=str(video_info['video_path']),
            tags=tags,
            publish_date=actual_publish_time,
            account_file=str(config['cookie']),
        )
        
        await video.main()
        return True, "上传成功"
    except Exception as e:
        return False, str(e)


async def main(target_date: str = None, dry_run: bool = False, platforms: list = None, schedule: bool = True):
    """主函数"""
    # 加载状态
    state = load_upload_state()
    
    # 查找要上传的视频
    videos = find_videos_to_upload(target_date)
    
    if not videos:
        print("没有找到需要上传的视频")
        return
    
    print(f"找到 {len(videos)} 个视频待上传\n")
    
    # 确定要上传的平台
    target_platforms = platforms or [p for p, c in PLATFORMS.items() if c['enabled']]
    
    for video_info in videos:
        video_key = str(video_info['video_path'])
        
        # 检查上传状态
        if video_key not in state['uploaded']:
            state['uploaded'][video_key] = {}
        
        # 计算发布时间
        video_index = list(video_info['video_path'].parent.glob('*.mp4')).index(video_info['video_path'])
        publish_time = get_publish_datetime(video_info['date'], video_index)
        
        # 如果发布时间已过，调整到明天
        now = datetime.now()
        if publish_time < now:
            # 保持原来的小时，但日期改为明天
            publish_time = now.replace(hour=publish_time.hour, minute=0, second=0) + timedelta(days=1)
        
        print(f"\n{'='*60}")
        print(f"📹 {video_info['video_path'].name}")
        print(f"   日期: {video_info['date']}")
        print(f"   发布时间: {publish_time.strftime('%Y-%m-%d %H:%M')}")
        
        for platform in target_platforms:
            if platform not in PLATFORMS:
                print(f"   ❌ 未知平台: {platform}")
                continue
            
            # 检查是否已上传
            if state['uploaded'][video_key].get(platform):
                print(f"   ✅ {platform}: 已上传")
                continue
            
            config = PLATFORMS[platform]
            success, message = await upload_to_platform(
                platform, config, video_info, publish_time, dry_run, schedule
            )
            
            if success and not dry_run:
                state['uploaded'][video_key][platform] = {
                    'time': datetime.now().isoformat(),
                    'publish_time': publish_time.isoformat(),
                }
                save_upload_state(state)
                print(f"   ✅ {platform}: {message}")
            elif not success:
                print(f"   ❌ {platform}: {message}")
    
    print(f"\n{'='*60}")
    print("上传完成!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='南荒说短视频多平台上传')
    parser.add_argument('--date', help='指定上传日期 (如 2026-02-05)')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要上传的内容')
    parser.add_argument('--platform', action='append', help='指定平台 (可多次使用)')
    parser.add_argument('--no-schedule', action='store_true', help='不使用定时发布，立即发布')
    
    args = parser.parse_args()
    
    asyncio.run(main(
        target_date=args.date,
        dry_run=args.dry_run,
        platforms=args.platform,
        schedule=not args.no_schedule,
    ))
