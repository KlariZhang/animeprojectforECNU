import pandas as pd

# 输入和输出路径
input_path = "newall.xlsx"  # 你的原始文件
output_path = "newall_cleaned.xlsx"  # 输出的新文件

# 读取所有 sheet
sheets = pd.read_excel(input_path, sheet_name=None)

# 存放处理后的结果
cleaned_sheets = {}

for sheet_name, df in sheets.items():
    # 删除 clean_name 重复的行，只保留一行
    df_unique = df.drop_duplicates(subset="clean_name", keep="first")

    # 只保留需要的列并改名
    df_result = df_unique[["clean_name", "常见IP","所属公司"]].rename(
        columns={"clean_name": "anime", "常见IP": "主要IP"}
    )

    # 存入字典
    cleaned_sheets[sheet_name] = df_result

# 写回新的 Excel，保持两个 sheet
with pd.ExcelWriter(output_path) as writer:
    for sheet_name, df in cleaned_sheets.items():
        df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"已生成文件: {output_path}")
