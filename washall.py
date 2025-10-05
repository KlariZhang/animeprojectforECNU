


import pandas as pd
import re

# 预编译正则表达式以提高效率
bracket_pattern1 = re.compile(r'（.*?）')
bracket_pattern2 = re.compile(r'\(.*?\)')
prefix_pattern = re.compile(r'^\d+[:：\s]?')
suffix_prefix_pattern = re.compile(r'\d+[:：\s]?.*$')

# 增强的后缀模式，包含更多常见后缀
suffix_pattern = re.compile(
    r'\s*(?:第[一二三四五六七八九十\d]*[季部]?|第\s*|[0-9]+[季部]?|'
    r'日语版|英语版|英文版|国语版|粤语版|未删减版|加长版|日文版|'
    r'上[篇部]|下[篇部]|前[篇部]|后[篇部]|特别篇|OVA|TV版|剧场版|动漫态|'
    r'动态漫|中配版|中文版|普通话版|粤配版|高清版|完整版|重制版|修复版|繁体'
    r'先行版|正式版|最终版|特别放送|最终话|总集篇|番外篇|'
    r'电影版|真人版|动画版|动画电影|剧场版动画)\s*$',
    re.IGNORECASE  # 忽略大小写
)

# 单独处理"第"字后无内容的情况
standalone_di_pattern = re.compile(r'\s*第\s*$')

def clean_anime_title(title):
    if not isinstance(title, str):
        return title

    # 1. 删除括号内的所有内容（中文或英文括号）
    title = bracket_pattern1.sub('', title)
    title = bracket_pattern2.sub('', title)

    # 2. 删除开头或末尾的数字 + 冒号或空格（序号/集数/季号等）
    title = prefix_pattern.sub('', title)  # 开头数字
    title = suffix_prefix_pattern.sub('', title)  # 末尾数字和冒号后的副标题

    # 3. 循环删除所有匹配的后缀（解决多个后缀问题）
    while True:
        new_title = suffix_pattern.sub('', title)
        # 额外处理单独的"第"字
        new_title = standalone_di_pattern.sub('', new_title)
        if new_title == title:  # 没有变化时退出循环
            break
        title = new_title

    # 4. 去掉首尾多余空格
    title = title.strip()

    return title

# 读取原 Excel
file_path = 'all.xlsx'
xls = pd.ExcelFile(file_path)
sheet_names = xls.sheet_names  # 获取所有 sheet 名称

# 创建一个字典存储清洗后的 sheet
cleaned_sheets = {}

for sheet_name in sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    original_col = df.columns[0]  # 假设第一列是动漫名称
    df['clean_name'] = df[original_col].apply(clean_anime_title)
    cleaned_sheets[sheet_name] = df

# 保存为新的 Excel 文件，包含所有 sheet
output_path = 'newall.xlsx'
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    for sheet_name, df in cleaned_sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"清洗完成，已保存至 {output_path}")