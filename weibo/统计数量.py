import csv

# 读取输入文件并统计每个关键词的帖子数
anime_count = {}

with open('weibo_anime_results_new.csv', 'r', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    next(reader)  # 跳过标题行
    for row in reader:
        if row:  # 确保行不为空
            keyword = row[0].strip()  # 获取关键词列，并去除空格
            if keyword in anime_count:
                anime_count[keyword] += 1
            else:
                anime_count[keyword] = 1

# 写入输出 CSV 文件
with open('anime_post_count.csv', 'w', encoding='utf-8', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['anime', '帖子数'])  # 写入标题行
    for anime, count in anime_count.items():
        writer.writerow([anime, count])

print("统计完成！结果已保存到 anime_post_count.csv")