import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
# --- 配置区 ---
# 1. 输入文件
INPUT_FILE = 'bilibili_stats.xlsx'  #选择数据文件名，确保文件格式正确（Excel，包含'anime'工作表）

# 2. 选择要对比的动漫IP 
ANIME_TO_PLOT =  pd.read_excel("bilibili_stats.xlsx",sheet_name = 'anime')["series_name"].head(10)


# 3. 选择要在雷达图上展示的维度/指标
# (选择有代表性的指标，太多会导致图表混乱，这里只是举几个例子
METRICS_TO_PLOT = [
    'total_views',
    'total_favorites',
    'total_danmakus',
    'total_likes',
    'total_coins',
    'latest_rating_score'
]

# 4. 输出图片文件名
OUTPUT_IMAGE_FILE = 'anime_radar_chart.png'
# --- 配置结束 ---


def create_radar_chart(file_path, anime_list, metrics):
    """
    根据给定的数据文件、动漫列表和指标，创建并保存雷达图。
    """
   
    
    # 1. 读取并准备数据
    try:
        df = pd.read_excel(file_path, sheet_name='anime')
        # 将动漫名称设为索引，方便查询
        df.set_index('series_name', inplace=True)
        print("[✓] 成功读取数据文件。")
    except FileNotFoundError:
        print(f"[!] 错误：数据文件 '{file_path}' 未找到。请确保文件名和路径正确。")
        return
    except Exception as e:
        print(f"[!] 读取文件时出错: {e}")
        return

    # 筛选出我们需要的数据（指定的IP和指标）
    try:
        data_to_plot = df.loc[anime_list, metrics]
    except KeyError as e:
        print(f"[!] 错误：找不到指定的动漫IP或指标: {e}。请检查配置区的名称是否正确。")
        return
        
    # 2. 数据归一化 
    # 雷达图要求所有维度都在同一个量级上，所以我们使用“最大-最小归一化”
    # 将每个指标的值都缩放到 0 到 1 的范围内
    data_normalized = (data_to_plot - data_to_plot.min()) / (data_to_plot.max() - data_to_plot.min())
    print("[✓] 数据归一化完成。")

    # 3. 准备绘图用的角度和标签
    labels = data_normalized.columns
    num_vars = len(labels)
    
    # 创建雷达图的角度
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    # 为了让多边形闭合，需要将第一个角度值再加到末尾
    angles += angles[:1]
    plt.style.use('seaborn-v0_8-darkgrid') # 使用一个更现代的风格
    # 4. 开始绘图
    # 设置中文字体，防止乱码

    # plt.rcParams['font.sans-serif'] = ['Heiti TC'] # Mac系统用 'Heiti TC' 或 'Arial Unicode MS'
    plt.rcParams['font.sans-serif'] = ['SimHei'] # Windows系统用 'SimHei'
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    colors = cm.get_cmap('cividis', len(data_normalized.index))(np.linspace(0, 1, len(data_normalized.index)))

    # 循环绘制每个动漫IP的多边形
    for i, (index, row) in enumerate(data_normalized.iterrows()):
        values = row.values.flatten().tolist()
        values += values[:1]
        ax.plot(angles, values, label=index, color=colors[i], linewidth=2.5) # 加粗线条
        ax.fill(angles, values, color=colors[i], alpha=0.2) # 调整透明度

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=14, color='grey') # 调整标签字体
    ax.tick_params(pad=20) # 增加标签与图的间距

    plt.title('国产动漫IP多维度对比雷达图', size=24, y=1.12)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=12)
    # --- 美化结束 ---
    
    # 添加标题和图例
    plt.title('国产动漫多维度对比雷达图', size=20, color='black', y=1.1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    # 6. 保存图表
    try:
        plt.savefig(OUTPUT_IMAGE_FILE, dpi=300, bbox_inches='tight')
        print(f" 图片已成功保存为 '{OUTPUT_IMAGE_FILE}'。")
    except Exception as e:
        print(f"[!] 保存图片时出错: {e}")

if __name__ == '__main__':
    create_radar_chart(INPUT_FILE, ANIME_TO_PLOT, METRICS_TO_PLOT)