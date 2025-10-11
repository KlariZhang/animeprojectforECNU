# -*- coding: utf-8 -*-
"""
Created on Tue Oct  7 12:16:01 2025

@author: HP
"""

"""
指标体系配置定义
定义三级指标到二级指标，二级指标到一级指标的映射关系
"""

# 三级指标到二级指标的映射
THIRD_TO_SECOND_MAPPING = {
    # 一级指标1: 内容价值
    "1.1.1": "1.1",  # 总播放量 -> 播放表现
    "1.1.2": "1.1",  # 追番人数/播放比 -> 播放表现
    "1.2.1": "1.2",  # 豆瓣评分 -> 口碑得分
    "1.2.2": "1.2",  # IMDb评分 -> 口碑得分
    "1.2.3": "1.2",  # B站评分 -> 口碑得分

    # 一级指标2: 讨论热度
    "2.1.1": "2.1",  # B站点赞数 -> 互动活跃度
    "2.1.2": "2.1",  # B站投币数 -> 互动活跃度
    "2.1.3": "2.1",  # B站收藏数 -> 互动活跃度
    "2.1.4": "2.1",  # B站分享数 -> 互动活跃度
    "2.1.5": "2.1",  # 豆瓣评论数 -> 互动活跃度
    "2.2.1": "2.2",  # B站二创视频数量 -> 同人二创
    "2.2.2": "2.2",  # 抖音二创视频数量 -> 同人二创
    "2.2.3": "2.2",  # 抖音二创点赞数 -> 同人二创
    "2.2.4": "2.2",  # 抖音二创评论数 -> 同人二创
    "2.2.5": "2.2",  # 抖音二创分享数 -> 同人二创
    "2.2.6": "2.2",  # 微博讨论帖子数 -> 同人二创
    "2.2.7": "2.2",  # 贴吧关注者数 -> 同人二创
    "2.2.8": "2.2",  # 贴吧帖子数 -> 同人二创
    "2.3.1": "2.3",  # B站评论条数 -> 评论分析

    # 一级指标3: 社会影响力
    "3.1.1": "3.1",  # 百度搜索量总和 -> 搜索热度
    "3.2.1": "3.2",  # 豆瓣评分人数 -> 口碑外溢
    "3.2.2": "3.2",  # IMDb评分人数 -> 口碑外溢
    "3.3.1": "3.3",  # IMDb评分 -> 出海表现

    # 一级指标4: 产业价值
    "4.1.1": "4.1",  # 游戏联动数量 -> 产业链延伸
    "4.1.2": "4.1",  # 演出信息数量 -> 产业链延伸
    "4.1.3": "4.1",  # 原作反哺数量 -> 产业链延伸
    "4.1.4": "4.1",  # 专利申请数 -> 产业链延伸
}

# 二级指标到一级指标的映射
SECOND_TO_FIRST_MAPPING = {
    "1.1": "1",  # 播放表现 -> 内容价值
    "1.2": "1",  # 口碑得分 -> 内容价值
    "2.1": "2",  # 互动活跃度 -> 讨论热度
    "2.2": "2",  # 同人二创 -> 讨论热度
    "2.3": "2",  # 评论分析 -> 讨论热度
    "3.1": "3",  # 搜索热度 -> 社会影响力
    "3.2": "3",  # 口碑外溢 -> 社会影响力
    "3.3": "3",  # 出海表现 -> 社会影响力
    "4.1": "4",  # 产业链延伸 -> 产业价值
}

# 三级指标对应的数据列名
THIRD_LEVEL_COLUMNS = {
    "1.1.1": "bilibili_movie_dataall_play_count_plays_log_minmax",
    "1.1.2": "bilibili_movie_dataall_followers_followers_log_minmax / bilibili_movie_dataall_play_count_plays_log_minmax",
    "1.2.1": "douban_movie_final_score_x_minmax",
    "1.2.2": "movie_imdb_final_new_rating_score_minmax",
    "1.2.3": "bilibili_movie_dataall_score_ratings_log_minmax",
    "2.1.1": "bilibili_movie_dataall_likes_interactions_log_minmax",
    "2.1.2": "bilibili_movie_dataall_coins_interactions_log_minmax",
    "2.1.3": "bilibili_movie_dataall_total_favorite_log_minmax",
    "2.1.4": "bilibili_movie_dataall_shares_interations_log_minmax",
    "2.1.5": "douban_movie_final_comment_count_log_minmax + douban_movie_final_review_count_log_minmax",
    "2.2.1": "bilibili_movie_creations_videos_log_minmax",
    "2.2.2": "douyin_movie_final_num_log_minmax",
    "2.2.3": "douyin_movie_final_likes_log_minmax",
    "2.2.4": "douyin_movie_final_comments_log_minmax",
    "2.2.5": "douyin_movie_final_shares_log_minmax",
    "2.2.6": "movie_post_count_movie_log_minmax",
    "2.2.7": "tieba_stats_from_excelmovie_new_followers_log_minmax",
    "2.2.8": "tieba_stats_from_excelmovie_new_posts_log_minmax",
    "2.3.1": "bilibili_movie_comments_comment_count_log_minmax",
    "3.1.1": "baidu_movie_index_summary_filled_sum_log_minmax",
    "3.2.1": "douban_movie_final_votes_douban_log_minmax",
    "3.2.2": "movie_imdb_final_new_rating_votes_log_minmax",
    "3.3.1": "movie_imdb_final_new_rating_score_minmax",  # 注意：与1.2.2重复，但属于不同维度
    "4.1.1": "complete_industry_movie_result_filled_game_count_minmax",
    "4.1.2": "complete_industry_movie_result_filled_show_count_minmax",
    "4.1.3": "complete_industry_movie_result_filled_work_count_minmax",
    "4.1.4": "complete_industry_movie_result_filled_patent_count_log_minmax",
}

# 一级指标名称映射（用于雷达图标签）
FIRST_LEVEL_NAMES = {
    "1": "内容价值",
    "2": "讨论热度",
    "3": "社会影响力",
    "4": "产业价值"
}


# 获取二级指标下的所有三级指标
def get_third_level_by_second(second_code):
    """根据二级指标代码获取其下属的所有三级指标代码"""
    return [third for third, second in THIRD_TO_SECOND_MAPPING.items() if second == second_code]


# 获取一级指标下的所有二级指标
def get_second_level_by_first(first_code):
    """根据一级指标代码获取其下属的所有二级指标代码"""
    return [second for second, first in SECOND_TO_FIRST_MAPPING.items() if first == first_code]


# 获取所有二级指标代码
def get_all_second_levels():
    """获取所有二级指标代码"""
    return list(set(THIRD_TO_SECOND_MAPPING.values()))


# 获取所有一级指标代码
def get_all_first_levels():
    """获取所有一级指标代码"""
    return list(set(SECOND_TO_FIRST_MAPPING.values()))