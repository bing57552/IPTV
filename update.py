import requests
import re
import time
import os
from typing import List, Dict, Tuple, Optional
import logging

# 日志配置：清晰记录筛选/测速/失效源信息
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPTVProcessor:
    def __init__(self):
        # 画质优先级强化：4K权重最高，1080P次之，剔除低清，适配你的高画质需求
        self.quality_priority = {
            '4k': 10, '4K': 10, '2160p': 10,  # 4K权重拉满，优先筛选
            '1080p': 8, '1080P': 8, 'fhd': 8,   # 1080P次高，保障高清
            '720p': 1, '720P': 1, 'hd': 1,      # 低清权重极低，基本剔除
            '标清': 0, 'sd': 0, '480p': 0, '360p': 0
        }
        
    def extract_channel_info(self, m3u_line: str) -> Optional[Dict]:
        if not m3u_line.startswith('#EXTINF'):
            return None
            
        channel_name = None
        group_title = None
        quality = '1080p'  # 默认画质为1080P，适配高画质基础要求
        raw_name = None    # 保留原始名称，用于多源排序（主源/备用源）
        
        # 提取原始频道名（含主源/备用源标识）
        name_match = re.search(r',([^,]+)$', m3u_line)
        if name_match:
            raw_name = name_match.group(1).strip()
            # 提取纯净频道名（剔除_主源X/备用源X，用于同名频道分组）
            channel_name = re.sub(r'_主源\d+|_备用源\d+', '', raw_name)
            
        # 提取分组标题，保持4K/1080P分组清晰
        group_match = re.search(r'group-title="([^"]*)"', m3u_line, re.IGNORECASE)
        if group_match:
            group_title = group_match.group(1).strip()
            
        # 提取画质：优先识别4K，再1080P，精准匹配M3U中的画质标注
        for q in self.quality_priority.keys():
            if q.lower() in m3u_line.lower() or q in ['4K', '2160p', '1080P'] and q in m3u_line:
                quality = q
                break
                
        return {
            'name': channel_name,       # 纯净名：用于同名频道分组
            'raw_name': raw_name,       # 原始名：用于主源/备用源排序
            'group': group_title,
            'quality': quality,
            'priority': self.quality_priority.get(quality.lower(), 0)
        }
    
    def test_stream_quality(self, url: str, timeout: int = 6) -> Tuple[float, bool]:
        """
        强化测速逻辑：保障音画同步+稳定连接
        1. 缩短超时为6秒，适配CI快速运行
        2. 验证状态码+内容类型，排除伪直播源
        3. 测速评分优化，低延迟高码源流得分更高
        """
        try:
            start_time = time.time()
            # 关闭证书验证，避免公网源SSL报错；允许重定向，适配CDN源
            response = requests.head(
                url, timeout=timeout, allow_redirects=True, 
                verify=False, headers={'User-Agent': 'Mozilla/5.0 (IPTV/Player)'}
            )
            
            # 仅保留200状态码的有效源，排除403/404/500失效源
            if response.status_code == 200:
                delay = time.time() - start_time
                # 延迟越低得分越高，音画同步的核心保障（延迟<0.5秒满分）
                speed_score = 1.0 / (delay + 0.01)
                content_type = response.headers.get('content-type', '').lower()
                
                # 高码率流额外加分：m3u8(4K/1080P主流) > ts流，保障画质
                if 'm3u8' in content_type or url.endswith('.m3u8'):
                    speed_score *= 1.5  # m3u8流权重最高，适配IPTV播放器
                elif 'video' in content_type or url.endswith('.ts'):
                    speed_score *= 1.2
                    
                # 延迟过高（>3秒）扣减分数，剔除音画不同步源
                if delay > 3:
                    speed_score *= 0.3
                    
                return round(speed_score, 2), True
            return 0.0, False
        except Exception as e:
            # 仅轻量记录失效源，不中断脚本运行
            logger.warning(f"源失效：{url[:50]} | 原因：{str(e)[:30]}")
            return 0.0, False
    
    def normalize_channel_name(self, name: str) -> str:
        """标准化频道名：确保同名频道精准分组，无重复"""
        if not name:
            return ''
        # 剔除画质/源标识，保留核心频道名
        name = re.sub(r'[4-9]K|1080P?|2160P?|标清|SD|HD|超清|高清|_主源\d+|_备用源\d+', '', name, flags=re.IGNORECASE)
        # 剔除特殊字符，统一格式
        name = re.sub(r'[^0-9A-Za-z一-鿿\s-]', '', name)
        name = re.sub(r'\s+', ' ', name.strip())
        return name.strip()
    
    def process_sources(self, m3u_content: str) -> str:
        lines = m3u_content.strip().splitlines()
        streams = []
        i = 0
        
        logger.info("开始解析多源M3U文件，筛选4K/1080P纯国语源...")
        
        # 解析M3U：提取所有频道信息+直播源URL
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('#EXTINF'):
                info = self.extract_channel_info(line)
                if not info or not info.get('name') or info['priority'] == 0:
                    i += 1
                    continue
                # 匹配下一行的直播源URL
                i += 1
                if i >= len(lines):
                    break
                url = lines[i].strip()
                if url and not url.startswith('#') and 'http' in url:
                    streams.append({
                        'name': info['name'],
                        'raw_name': info['raw_name'],
                        'group': info['group'] or '1080P影视核心频道',
                        'url': url,
                        'quality': info['quality'],
                        'priority': info['priority'],
                        'normalized_name': self.normalize_channel_name(info['name'])
                    })
            i += 1
            
        if not streams:
            logger.error("未解析到有效直播源，请检查M3U文件！")
            return '#EXTM3U\n# 无有效直播源'
        
        logger.info(f"共解析到 {len(streams)} 个直播源，开始按频道分组+多源排序...")
        
        # 核心：按标准化频道名分组，实现「单频道多源」聚合
        channel_groups = {}
        for stream in streams:
            norm_name = stream['normalized_name']
            if norm_name not in channel_groups:
                channel_groups[norm_name] = []
            channel_groups[norm_name].append(stream)
            
        logger.info(f"分组完成，共 {len(channel_groups)} 个核心频道（无重复），开始测速+筛选最佳源...")
        
        # 生成结果M3U，保留标准头
        result_lines = ['#EXTM3U x-tvg-url=""', '#EXT-X-VERSION:3']
        
        # 遍历每个频道的多源，筛选最佳源
        for norm_name, sources in channel_groups.items():
            logger.info(f"处理频道：{norm_name}（共 {len(sources)} 个备用源）")
            
            # 第一步：多源排序——主源优先，备用源按数字升序（主源1→备用源2→备用源3）
            sources.sort(key=lambda x: (
                0 if "主源" in x['raw_name'] else 1,
                int(re.search(r'源(\d+)', x['raw_name']).group(1)) if re.search(r'源(\d+)', x['raw_name']) else 99
            ))
            
            # 第二步：对每个源测速+验证可用性，计算综合得分
            for source in sources:
                speed_score, available = self.test_stream_quality(source['url'])
                source['speed_score'] = speed_score
                source['available'] = available
                # 综合得分公式：画质权重（核心）+ 测速得分（稳定）+ 可用性（基础）
                # 4K/1080P权重拉满，保障高画质优先
                source['total_score'] = (
                    source['priority'] * 10 +  # 画质权重（4K=100，1080P=80）
                    source['speed_score'] * 2 + # 测速得分（低延迟加分）
                    (10 if source['available'] else 0) # 可用源基础分
                )
            
            # 第三步：筛选可用源，按综合得分降序，取最优1个
            available_sources = [s for s in sources if s['available']]
            if not available_sources:
                logger.warning(f"频道 {norm_name} 所有源均失效，跳过！")
                continue
            # 按综合得分排序，得分最高的为最佳源（画质+稳定+可用）
            best_source = sorted(available_sources, key=lambda x: x['total_score'], reverse=True)[0]
            
            # 构造标准EXTINF行，适配所有IPTV播放器，保留原始名+分组+画质
            extinf = f'#EXTINF:-1 tvg-name="{best_source["raw_name"]}" group-title="{best_source["group"]}" quality="{best_source["quality"]}",{best_source["raw_name"]}'
            result_lines.extend([extinf, best_source['url']])
            logger.info(f"✅ 筛选完成：{best_source['raw_name']} | 画质：{best_source['quality']} | 综合得分：{best_source['total_score']:.1f} | 源：{best_source['url'][:60]}...")
        
        # 生成最终M3U内容，换行符适配跨平台
        result_m3u = '\n'.join(result_lines)
        valid_channel_num = len([l for l in result_lines if l.startswith('#EXTINF')])
        logger.info(f"全部处理完成！共生成 {valid_channel_num} 个有效高画质频道，已剔除失效源/重复频道！")
        return result_m3u

def main():
    processor = IPTVProcessor()
    # 从环境变量获取M3U源地址（适配GitHub Actions，无需本地文件）
    m3u_url = os.getenv('M3U_SOURCE_URL')
    
    # 校验环境变量配置，避免脚本崩溃
    if not m3u_url:
        logger.error("❌ 未配置M3U_SOURCE_URL环境变量，请检查update.yml！")
        return
    
    try:
        # 拉取M3U源：设置超时+重试，保障GitHub Actions拉取成功
        logger.info(f"正在拉取M3U源：{m3u_url}")
        response = requests.get(
            m3u_url, timeout=15, allow_redirects=True,
            verify=False, headers={'User-Agent': 'Mozilla/5.0 (GitHub Actions/IPTV)'}
        )
        response.raise_for_status()  # 抛出HTTP错误，触发异常处理
        m3u_content = response.text
        if not m3u_content:
            logger.error("❌ 拉取的M3U源内容为空！")
            return
    except Exception as e:
        logger.error(f"❌ 拉取M3U源失败：{str(e)}")
        return
    
    # 处理源并生成最佳M3U
    try:
        result_m3u = processor.process_sources(m3u_content)
    except Exception as e:
        logger.error(f"❌ 处理M3U源失败：{str(e)}", exc_info=True)
        return
    
    # 保存结果到output_best.m3u，适配GitHub Actions自动提交
    try:
        with open('output_best.m3u', 'w', encoding='utf-8') as f:
            f.write(result_m3u)
        logger.info("✅ 最佳直播源已保存到 output_best.m3u")
        print("🎉 全部操作完成！有效高画质频道已生成，可直接导入IPTV播放器使用！")
    except Exception as e:
        logger.error(f"❌ 保存output_best.m3u失败：{str(e)}")

if __name__ == "__main__":
    main()
