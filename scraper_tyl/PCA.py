# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS 自带的中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def safe_read_csv(file_path, encoding_list=['utf-8', 'gbk', 'gb18030', 'latin1']):
    """
    读取CSV文件
    """
    for encoding in encoding_list:
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法用{encoding_list}中的任何编码读取文件: {file_path}")


def load_and_merge_data(data_dir):
    """
    从各平台CSV文件加载数据并合并为一个完整的数据集
    """
    # 初始化一个空DataFrame，以电影名称为索引
    df = pd.DataFrame(index=['电影 A', '电影 B', '电影 C'])

    try:
        # 1. 百度指数数据
        baidu_path = os.path.join(data_dir, 'baidu_index.csv')
        if os.path.exists(baidu_path):
            baidu_df = safe_read_csv(baidu_path)
            df['百度指数'] = baidu_df.set_index('movie')['baidu_index']

        # 2. B站数据
        bilibili_path = os.path.join(data_dir, 'bilibili.csv')
        if os.path.exists(bilibili_path):
            bilibili_df = safe_read_csv(bilibili_path)
            # 主数据
            df['B站播放量'] = bilibili_df.set_index('movie')['play_count_plays']
            df['B站粉丝数'] = bilibili_df.set_index('movie')['followers_followers']
            df['B站点赞数'] = bilibili_df.set_index('movie')['likes_interactions']
            df['B站投币数'] = bilibili_df.set_index('movie')['coins_interactions']
            df['B站收藏数'] = bilibili_df.set_index('movie')['favorites_interactions']
            df['B站分享数'] = bilibili_df.set_index('movie')['shares_interactions']
            df['B站评论数'] = bilibili_df.set_index('movie')['comments_interactions']
            df['B站弹幕数'] = bilibili_df.set_index('movie')['danmu_interactions']
            df['B站评分'] = bilibili_df.set_index('movie')['score_ratings']

        # 3. 票房数据
        boxoffice_path = os.path.join(data_dir, 'boxoffice.csv')
        if os.path.exists(boxoffice_path):
            boxoffice_df = safe_read_csv(boxoffice_path)
            df['票房(元)'] = boxoffice_df.set_index('movie')['box_office']

        # 4. 豆瓣数据
        douban_path = os.path.join(data_dir, 'douban.csv')
        if os.path.exists(douban_path):
            douban_df = safe_read_csv(douban_path)
            df['豆瓣评分'] = douban_df.set_index('movie')['score_x']
            df['豆瓣投票数'] = douban_df.set_index('movie')['votes_douban']
            df['豆瓣评论数'] = douban_df.set_index('movie')['comment_count']

        # 5. 抖音数据
        douyin_path = os.path.join(data_dir, 'douyin.csv')
        if os.path.exists(douyin_path):
            douyin_df = safe_read_csv(douyin_path)
            df['抖音点赞数'] = douyin_df.set_index('movie')['likes']
            df['抖音评论数'] = douyin_df.set_index('movie')['comments']
            df['抖音分享数'] = douyin_df.set_index('movie')['shares']

        # 6. 骨朵数据
        guduo_path = os.path.join(data_dir, 'guduo.csv')
        if os.path.exists(guduo_path):
            guduo_df = safe_read_csv(guduo_path)
            df['骨朵播放量'] = guduo_df.set_index('电影名称')['play_count_plays']

        # 7. IMDB数据
        imdb_path = os.path.join(data_dir, 'imdb.csv')
        if os.path.exists(imdb_path):
            imdb_df = safe_read_csv(imdb_path)
            df['IMDB评分'] = imdb_df.set_index('movie')['score_y']
            df['IMDB投票数'] = imdb_df.set_index('movie')['votes_imdb']
            df['IMDB排名'] = imdb_df.set_index('movie')['rank']

        # 8. 行业衍生数据
        industry_path = os.path.join(data_dir, 'industry.csv')
        if os.path.exists(industry_path):
            industry_df = safe_read_csv(industry_path)
            df['游戏数量'] = industry_df.set_index('movie')['game_count']
            df['节目数量'] = industry_df.set_index('movie')['show_count']
            df['原作数量'] = industry_df.set_index('movie')['work_count']
            df['专利数量'] = industry_df.set_index('movie')['patent_count']

        # 9. 风险数据
        risk_path = os.path.join(data_dir, 'risk.csv')
        if os.path.exists(risk_path):
            risk_df = safe_read_csv(risk_path)
            df['负面评价比例'] = risk_df.set_index('movie')['negative_ratio']

        # 10. 淘宝闲鱼数据
        taobao_path = os.path.join(data_dir, 'taobao_xianyu.csv')
        if os.path.exists(taobao_path):
            taobao_df = safe_read_csv(taobao_path)
            df['淘宝销量'] = taobao_df.set_index('movie')['taobao']
            df['闲鱼销量'] = taobao_df.set_index('movie')['xianyu']

        # 11. 腾讯视频数据
        tencent_path = os.path.join(data_dir, 'tencent.csv')
        if os.path.exists(tencent_path):
            tencent_df = safe_read_csv(tencent_path)
            df['腾讯播放量'] = tencent_df.set_index('电影名称')['play_count_plays']

        # 12. 贴吧数据
        tieba_path = os.path.join(data_dir, 'tieba.csv')
        if os.path.exists(tieba_path):
            tieba_df = safe_read_csv(tieba_path)
            df['贴吧帖子数'] = tieba_df.set_index('movie')['posts']
            df['贴吧粉丝数'] = tieba_df.set_index('movie')['followers']

        # 13. 微博数据
        weibo_path = os.path.join(data_dir, 'weibo.csv')
        if os.path.exists(weibo_path):
            weibo_df = safe_read_csv(weibo_path)
            df['微博讨论数'] = weibo_df.set_index('movie')['posts']

        # 14. 优酷数据
        youku_path = os.path.join(data_dir, 'youku.csv')
        if os.path.exists(youku_path):
            youku_df = safe_read_csv(youku_path)
            df['优酷播放量'] = youku_df.set_index('电影名称')['play_count_plays']

        return df

    except Exception as e:
        print(f"加载数据时出错: {str(e)}")
        return None


def perform_pca_analysis(df):
    """
    执行PCA分析并可视化结果
    """
    if df is None or df.empty:
        print("数据为空，无法执行PCA分析")
        return None

    # 数据标准化
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)

    # 执行PCA
    pca = PCA()
    pca_results = pca.fit_transform(scaled_data)

    # 创建包含主成分的DataFrame
    pca_df = pd.DataFrame(data=pca_results,
                          columns=[f'PC{i + 1}' for i in range(pca_results.shape[1])],
                          index=df.index)

    # 1. 解释方差分析
    explained_variance = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(explained_variance)

    plt.figure(figsize=(10, 6))
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS 自带的中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.bar(range(1, len(explained_variance) + 1), explained_variance, alpha=0.5,
            align='center', label='单个主成分解释方差')
    plt.step(range(1, len(cumulative_variance) + 1), cumulative_variance,
             where='mid', label='累计解释方差')
    plt.ylabel('解释方差比例')
    plt.xlabel('主成分序号')
    plt.xticks(range(1, len(explained_variance) + 1))
    plt.legend(loc='best')
    plt.title('主成分分析 - 解释方差比例')
    plt.tight_layout()
    plt.show()

    # 打印解释方差
    print("=== 解释方差比例 ===")
    for i, var in enumerate(explained_variance):
        print(f"PC{i + 1}: {var:.4f} ({var * 100:.2f}%)")

    print("\n=== 累计解释方差 ===")
    for i, var in enumerate(cumulative_variance):
        print(f"前{i + 1}个主成分: {var:.4f} ({var * 100:.2f}%)")

    # 2. 主成分散点图
    plt.figure(figsize=(10, 8))
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS 自带的中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    scatter = plt.scatter(pca_df['PC1'], pca_df['PC2'], s=200, alpha=0.7)
    for i, txt in enumerate(pca_df.index):
        plt.annotate(txt, (pca_df['PC1'][i], pca_df['PC2'][i]),
                     fontsize=12, xytext=(5, 5), textcoords='offset points')
    plt.xlabel(f'第一主成分 PC1 ({explained_variance[0] * 100:.2f}%)')
    plt.ylabel(f'第二主成分 PC2 ({explained_variance[1] * 100:.2f}%)')
    plt.title('主成分分析 - 电影分布')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    # 3. 主成分载荷分析
    loadings = pd.DataFrame(pca.components_.T * np.sqrt(pca.explained_variance_),
                            columns=[f'PC{i + 1}' for i in range(pca.components_.shape[0])],
                            index=df.columns)

    # 可视化前两个主成分的载荷
    plt.figure(figsize=(12, 8))
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # macOS 自带的中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    plt.scatter(loadings['PC1'], loadings['PC2'], alpha=0.5)
    for i, txt in enumerate(loadings.index):
        plt.annotate(txt, (loadings['PC1'][i], loadings['PC2'][i]),
                     fontsize=10, xytext=(5, 5), textcoords='offset points')
    plt.xlabel(f'PC1载荷 ({explained_variance[0] * 100:.2f}%)')
    plt.ylabel(f'PC2载荷 ({explained_variance[1] * 100:.2f}%)')
    plt.title('主成分载荷分析')
    plt.axhline(0, color='grey', linestyle='--')
    plt.axvline(0, color='grey', linestyle='--')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()

    # 4. 热力图显示前N个主成分的载荷
    plt.figure(figsize=(12, 8))
    top_n = min(5, loadings.shape[1])  # 显示前5个主成分
    sns.heatmap(loadings.iloc[:, :top_n],
                cmap='coolwarm',
                annot=True,
                fmt=".2f",
                linewidths=0.5,
                cbar_kws={'label': '载荷值'})
    plt.title('主成分载荷热力图')
    plt.tight_layout()
    plt.show()

    # 5. 返回分析结果
    return {
        'pca_model': pca,
        'pca_results': pca_df,
        'loadings': loadings,
        'explained_variance': explained_variance,
        'cumulative_variance': cumulative_variance
    }


def interpret_pca_results(results):
    """
    解释PCA分析结果
    """
    if results is None:
        print("没有可解释的结果")
        return

    print("\n=== PCA分析结果解释 ===")

    # 解释前几个主成分
    for i in range(2):  # 解释前两个主成分
        pc = f'PC{i + 1}'
        print(f"\n【{pc} 解释】:")

        # 获取载荷绝对值最大的10个特征
        top_features = results['loadings'][pc].abs().sort_values(ascending=False).head(10)

        print(f"主要代表以下指标(按重要性排序):")
        for feature, loading in top_features.items():
            direction = "正向" if results['loadings'].loc[feature, pc] > 0 else "负向"
            print(f"- {feature}: {direction}影响 (载荷值: {loading:.3f})")

        # 简单总结
        if i == 0:
            print("\n总结: PC1通常代表综合热度/影响力指标")
        elif i == 1:
            print("\n总结: PC2通常代表质量/口碑相关指标")


# 主程序
if __name__ == "__main__":
    # 设置数据目录路径
    data_directory = "/Users/chenyaxin/Desktop/ECNU/b站行业分析项目/指标体系/movie_data_structures"

    # 1. 加载并合并数据
    print("正在加载数据...")
    movie_data = load_and_merge_data(data_directory)

    if movie_data is None:
        print("无法加载数据，请检查数据文件和路径")
        exit()

    # 检查数据
    print("\n=== 数据概览 ===")
    print(movie_data.head())
    print(f"\n数据形状: {movie_data.shape}")

    # 2. 执行PCA分析
    print("\n正在执行PCA分析...")
    pca_results = perform_pca_analysis(movie_data)

    # 3. 解释结果
    interpret_pca_results(pca_results)

    print("\nPCA分析完成!")