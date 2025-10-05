import requests
import pandas as pd
from datetime import datetime
import time
import json
import re
import os


class DouyinAnalyzer:
    """
    抖音数据分析工具类，整合了抖音搜索和热点宝数据抓取功能
    """

    def __init__(self):
        # API配置
        self.DOUYIN_API = {
            'search': 'https://www.douyin.com/aweme/v1/web/general/search/single/',
            'video_detail': 'https://www.douyin.com/aweme/v1/web/aweme/detail/',
            'douhot': 'https://douhot.douyin.com/douhot/v1/material/video_billboard'
        }

        # 请求头
        self.HEADERS = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Referer': 'https://www.douyin.com/'
        }

        # 榜单类型映射
        self.RANK_TYPES = {
            'video': '视频总榜',
            'low_fans': '低粉爆款',
            'high_play_rate': '高完播率',
            'high_fans_rate': '高涨粉率',
            'high_like_rate': '高点赞率'
        }

        self.TIME_RANGES = {
            'hour': '近1小时',
            'day': '近1天',
            '3day': '近3天',
            'week': '近7天'
        }

        # 创建数据存储目录
        self.DATA_DIR = 'douyin_data'
        os.makedirs(self.DATA_DIR, exist_ok=True)

        # 初始化cookies
        self.cookies = None

    # ==================== 通用工具函数 ====================

    def get_douyin_cookies(self):
        """获取抖音必要的cookies（需要手动获取一次）"""
        print("请按以下步骤获取cookies：")
        print("1. 用Chrome访问 https://www.douyin.com")
        print("2. 登录你的账号")
        print("3. 按F12打开开发者工具 -> Application -> Cookies")
        print("4. 复制'ttwid'和's_v_web_id'的值")

        cookies = {
            'ttwid': input("请输入ttwid的值: ").strip(),
            's_v_web_id': input("请输入s_v_web_id的值: ").strip()
        }

        # 保存cookies
        with open('douyin_cookies.json', 'w') as f:
            json.dump(cookies, f)

        self.cookies = cookies
        return cookies

    def load_cookies(self):
        """加载cookies"""
        try:
            with open('douyin_cookies.json', 'r') as f:
                self.cookies = json.load(f)
            print("[+] 检测到已有cookies文件")
            return True
        except:
            print("[-] 未检测到cookies文件，需要手动获取")
            return False

    def parse_video_count(self, count_str):
        """处理抖音的计数单位（万/亿）"""
        if count_str is None:
            return 0
        if '万' in count_str:
            return int(float(count_str.replace('万', '')) * 10000)
        elif '亿' in count_str:
            return int(float(count_str.replace('亿', '')) * 100000000)
        return int(count_str)

    # ==================== 抖音搜索功能 ====================

    def search_douyin_videos(self, keyword, max_results=50):
        """搜索抖音视频（带分页功能）"""
        if not self.cookies:
            if not self.load_cookies():
                self.cookies = self.get_douyin_cookies()

        base_params = {
            'device_platform': 'webapp',
            'aid': '6383',
            'channel': 'channel_pc_web',
            'search_channel': 'aweme_video_web',
            'sort_type': '0',
            'publish_time': '0',
            'keyword': keyword,
            'search_source': 'normal_search',
            'query_correct_type': '1',
            'is_filter_search': '0',
            'count': '20'  # 每次请求最多20条
        }

        videos = []
        offset = 0
        retry_count = 0
        max_retries = 3

        while len(videos) < max_results and retry_count < max_retries:
            try:
                params = base_params.copy()
                params['offset'] = str(offset)

                response = requests.get(
                    self.DOUYIN_API['search'],
                    params=params,
                    headers=self.HEADERS,
                    cookies=self.cookies,
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()

                if data.get('status_code') == 0:
                    new_videos = 0
                    for item in data.get('data', []):
                        if item.get('type') == 1:  # 视频类型
                            aweme_info = item.get('aweme_info', {})
                            if aweme_info.get('is_ads') is True:
                                continue  # 跳过广告

                            videos.append({
                                '视频ID': aweme_info.get('aweme_id'),
                                '描述': aweme_info.get('desc', ''),
                                '作者': aweme_info.get('author', {}).get('nickname', ''),
                                '作者ID': aweme_info.get('author', {}).get('uid', ''),
                                '播放量': aweme_info.get('statistics', {}).get('play_count', 0),
                                '点赞数': aweme_info.get('statistics', {}).get('digg_count', 0),
                                '评论数': aweme_info.get('statistics', {}).get('comment_count', 0),
                                '分享数': aweme_info.get('statistics', {}).get('share_count', 0),
                                '收藏数': aweme_info.get('statistics', {}).get('collect_count', 0),
                                '视频链接': f"https://www.douyin.com/video/{aweme_info.get('aweme_id')}",
                                '发布时间': datetime.fromtimestamp(aweme_info.get('create_time', 0)).strftime(
                                    '%Y-%m-%d %H:%M:%S'),
                                '是否二创': False  # 初始化为False，将在后续判断
                            })
                            new_videos += 1

                            if len(videos) >= max_results:
                                break

                    print(f"已获取 {len(videos)}/{max_results} 条视频数据")

                    # 如果没有新数据，可能已经到达末尾
                    if new_videos == 0:
                        print("没有更多数据了")
                        break

                    # 准备下一次请求
                    offset += 20
                    retry_count = 0  # 重置重试计数

                    # 避免请求过于频繁
                    time.sleep(1)

                else:
                    print(f"API返回错误: {data.get('message')}")
                    retry_count += 1
                    time.sleep(2)

            except Exception as e:
                print(f"请求失败: {e}")
                retry_count += 1
                time.sleep(2)

        print(f"成功获取 {len(videos)} 条抖音视频数据")
        return videos

    def is_creative_video(self, video, keyword):
        """增强版二创识别（针对动漫内容优化）"""
        desc = video.get('描述', '') or ''
        author = video.get('作者', '') or ''
        desc = desc.lower()
        author = author.lower()

        # 排除官方账号（根据实际需要添加）
        official_accounts = ['非人哉官方', '非人哉动画']
        if any(acc.lower() in author for acc in official_accounts):
            return False

        # 二创作特征关键词（新增动漫相关）
        positive_indicators = [
            # 创作形式
            '二创', '剪辑', '混剪', 'amv', 'mad', 'mmd',
            '手书', 'reaction', '配音', '鬼畜', '手绘',
            '翻唱', '翻跳', '翻奏', '翻拍', '同人曲',
            '手写', '手作', '手工', '手账', '手办',
            'cos', 'cosplay', '角色扮演',
            # 内容特征
            '同人', '玩梗', '名场面', '高能片段', '名台词',
            '自制', '粉丝向', '二改', '改编', '恶搞',
            '解说', '盘点', '合集', '串烧', '混搭',
            '创意', '脑洞', '创意剪辑', '创意视频',
            '粉丝制作', '饭制', '饭剪', '饭绘',
            '同人图', '同人文', '同人视频', '同人动画',
            '手绘动画', '手绘视频', '手绘漫画',
            '原创', '原创视频', '原创动画', '原创音乐'
        ]

        # 官方内容特征（需排除）
        negative_indicators = [
            '官方', '预告', '正片', '全集', '完整版',
            '定档', '剧场版', '第.*季', '第.*集',
            '上映', '首播', '大电影', '电影版',
            '正版', '授权', '合作', '联名',
            '花絮', '幕后', '制作过程'
        ]

        # 判定条件（满足任意创作特征且无官方特征）
        has_creative = any(kw in desc or kw in author for kw in positive_indicators)
        not_official = not any(re.search(kw, desc) for kw in negative_indicators)

        # 额外条件：如果视频描述中包含关键词但没有任何创作特征，则认为是官方内容
        if keyword.lower() in desc and not has_creative:
            return False

        return has_creative and not_official

    def analyze_creative_videos(self, keyword):
        """
        分析二创视频数据
        返回:
        - 所有视频数据（包含是否二创标记）
        - 统计结果
        """
        print(f"\n开始分析「{keyword}」的二创视频数据...")

        # 获取原始视频数据
        all_videos = self.search_douyin_videos(keyword, max_results=50)
        if not all_videos:
            return None, None

        # 标记二创视频
        for video in all_videos:
            try:
                video['是否二创'] = self.is_creative_video(video, keyword)
            except Exception as e:
                print(f"处理视频时出错: {e}")
                print(f"问题视频数据: {video}")
                video['是否二创'] = False

        # 筛选二创视频
        creative_videos = [v for v in all_videos if v['是否二创']]

        if not creative_videos:
            print("\n调试信息：前10条视频详情：")
            for i, v in enumerate(all_videos[:10], 1):
                print(f"{i}. 作者: {v.get('作者', '未知')}")
                print(f"   描述: {v.get('描述', '无描述')[:60]}...")
                print(f"   播放: {v.get('播放量', 0)} | 点赞: {v.get('点赞数', 0)}")
                print(f"   是否二创: {v.get('是否二创', False)}")
                print("-" * 50)
            print("\n未识别到二创视频，请检查关键词或调整识别规则")
            return all_videos, None

        # 计算平均播放量
        avg_play = sum(v.get('播放量', 0) for v in creative_videos) / len(creative_videos)

        # 获取头部视频（按播放量排序）
        top_videos = sorted(creative_videos, key=lambda x: x.get('播放量', 0), reverse=True)[:3]

        # 计算二创占比
        creative_ratio = len(creative_videos) / len(all_videos) * 100

        # 统计结果
        stats = {
            '关键词': keyword,
            '二创视频数量': len(creative_videos),
            '总视频数量': len(all_videos),
            '二创占比(%)': round(creative_ratio, 2),
            '平均播放量': int(avg_play),
            '头部视频': top_videos
        }

        return all_videos, stats

    def save_search_results(self, all_videos, stats, keyword):
        """保存搜索结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存所有视频数据
        if all_videos:
            all_videos_filename = os.path.join(self.DATA_DIR, f"douyin_all_videos_{keyword}_{timestamp}.json")
            with open(all_videos_filename, 'w', encoding='utf-8') as f:
                json.dump(all_videos, f, ensure_ascii=False, indent=2)
            print(f"\n所有视频数据已保存到: {all_videos_filename}")

            # 保存二创视频数据
            creative_videos = [v for v in all_videos if v['是否二创']]
            if creative_videos:
                creative_filename = os.path.join(self.DATA_DIR, f"douyin_creative_videos_{keyword}_{timestamp}.json")
                with open(creative_filename, 'w', encoding='utf-8') as f:
                    json.dump(creative_videos, f, ensure_ascii=False, indent=2)
                print(f"二创视频数据已保存到: {creative_filename}")

        # 保存统计结果
        if stats:
            stats_filename = os.path.join(self.DATA_DIR, f"douyin_stats_{keyword}_{timestamp}.json")
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"统计数据已保存到: {stats_filename}")

            # 打印分析结果
            print("\n=== 分析结果 ===")
            print(f"关键词: {stats['关键词']}")
            print(f"二创视频数量: {stats['二创视频数量']}/{stats['总视频数量']}")
            print(f"二创视频占比: {stats['二创占比(%)']}%")
            print(f"平均播放量: {stats['平均播放量']}")

            print("\n=== 头部二创视频 ===")
            for i, video in enumerate(stats['头部视频'], 1):
                print(f"{i}. {video.get('描述', '无描述')}")
                print(
                    f"   作者: {video.get('作者', '未知')} | 播放: {video.get('播放量', 0)} | 点赞: {video.get('点赞数', 0)}")
                print(f"   链接: {video.get('视频链接', '无链接')}")
        else:
            print("分析失败，请检查网络或关键词是否正确")

    # ==================== 热点宝功能 ====================

    def fetch_douhot_videos(self, keyword=None, rank_type='video', time_range='day', category_id=1001):
        """
        获取抖音热点宝视频榜数据
        """
        params = {
            'active_tab': 'hotspot_video',
            'date_window': {
                'hour': '1',
                'day': '24',
                '3day': '72',
                'week': '168'
            }.get(time_range, '24'),
            'sub_type': str(category_id),
            'rank_type': rank_type
        }

        if keyword:
            params['keyword'] = keyword

        print(
            f"[*] 正在获取抖音热点宝{self.RANK_TYPES.get(rank_type, rank_type)}数据(时间:{self.TIME_RANGES.get(time_range, time_range)})...")

        try:
            response = requests.get(
                self.DOUYIN_API['douhot'],
                params=params,
                headers=self.HEADERS,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            print(f"API返回数据: {data}")  # 调试输出

            # 检查API返回状态
            if data.get('status_code') == 0:
                video_list = data.get('data', {}).get('list', [])
                if video_list:
                    print(f"成功获取到 {len(video_list)} 条视频数据.")
                    return video_list
                else:
                    print("[!] API返回成功，但视频列表为空.")
            else:
                print(f"[!] API返回错误: {data.get('message', '未知错误')}")

            return None

        except Exception as e:
            print(f"[!] 请求过程中发生错误: {str(e)}")
            return None

    def process_douhot_data(self, raw_data):
        """
        处理热点宝返回的视频数据
        """
        processed = []
        for item in raw_data:
            video_info = item.get('video_info', {})
            author_info = item.get('author_info', {})

            processed.append({
                '排名': item.get('rank', 0),
                '视频标题': video_info.get('title', '无标题'),
                '热度值': item.get('hot_value', 0),
                '播放量': video_info.get('play_count', 0),
                '点赞量': video_info.get('digg_count', 0),
                '作者': author_info.get('nickname', '未知'),
                '作者粉丝数': author_info.get('follower_count', 0),
                '发布时间': datetime.fromtimestamp(video_info.get('create_time', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                '视频链接': f"https://www.douyin.com/video/{video_info.get('aweme_id', '')}"
            })
        return processed

    def save_douhot_results(self, processed_data, rank_type, time_range):
        """保存热点宝结果"""
        df = pd.DataFrame(processed_data)

        # 生成文件名
        current_time = datetime.now().strftime("%Y%m%d_%H%M")
        file_name = os.path.join(self.DATA_DIR, f"douyin_hotspot_{rank_type}_{time_range}_{current_time}.csv")

        try:
            # 保存到CSV
            df.to_csv(file_name, index=False, encoding='utf-8-sig')
            print(f"任务完成！数据已成功保存至文件: {file_name}")
            print("\n文件内容预览:")
            print(df.head())
        except Exception as e:
            print(f"\n[!] 文件保存失败: {e}")

    # ==================== 主菜单 ====================

    def run_search_analysis(self):
        """运行搜索分析功能"""
        print("抖音二创视频分析爬虫 v1.4")
        print("=" * 50)

        # 1. 获取必要cookies
        if not self.load_cookies():
            self.cookies = self.get_douyin_cookies()

        # 2. 获取用户输入
        keyword = input("\n请输入要分析的动漫/游戏名称: ").strip()
        if not keyword:
            print("输入不能为空！")
            return

        # 3. 执行分析
        all_videos, stats = self.analyze_creative_videos(keyword)
        self.save_search_results(all_videos, stats, keyword)

    def run_douhot_analysis(self):
        """运行热点宝分析功能"""
        print("抖音热点宝视频榜数据爬虫")
        print("=" * 50)

        # 获取用户输入
        keyword = input("请输入搜索关键词(可选，直接回车跳过): ").strip()

        print("\n可选榜单类型:")
        for key, value in self.RANK_TYPES.items():
            print(f"{key}: {value}")
        rank_type = input("\n选择榜单类型(默认video): ").strip() or 'video'

        print("\n可选时间范围: hour(近1小时), day(近1天), 3day(近3天), week(近7天)")
        time_range = input("选择时间范围(默认day): ").strip() or 'day'

        category_id = input("输入垂类ID(默认1001): ").strip() or '1001'

        # 获取数据
        raw_data = self.fetch_douhot_videos(
            keyword=keyword if keyword else None,
            rank_type=rank_type,
            time_range=time_range,
            category_id=int(category_id)
        )

        if raw_data:
            # 处理数据
            processed_data = self.process_douhot_data(raw_data)
            self.save_douhot_results(processed_data, rank_type, time_range)

    def main_menu(self):
        """主菜单"""
        while True:
            print("\n=== 抖音数据分析工具 ===")
            print("1. 抖音二创视频分析")
            print("2. 抖音热点宝数据分析")
            print("3. 退出")

            choice = input("\n请选择功能(1-3): ").strip()

            if choice == '1':
                self.run_search_analysis()
            elif choice == '2':
                self.run_douhot_analysis()
            elif choice == '3':
                print("感谢使用，再见！")
                break
            else:
                print("无效输入，请重新选择！")

            input("\n按回车键返回主菜单...")


if __name__ == "__main__":
    analyzer = DouyinAnalyzer()
    analyzer.main_menu()1