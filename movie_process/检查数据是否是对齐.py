import pandas as pd
from sqlalchemy import create_engine


def compare_columns(data1, data2, column_name, data1_name="表1", data2_name="表2",
                    data1_id_col=None, data2_id_col=None, db_connection=None):
    """
    检查两个表的某一列内容是否完全相同

    参数:
    data1: 第一个数据源 (DataFrame, 数据库表名或文件路径)
    data2: 第二个数据源 (DataFrame, 数据库表名或文件路径)
    column_name: 要比较的列名
    data1_name: 第一个表的标识名称
    data2_name: 第二个表的标识名称
    data1_id_col: 表1的主键列（用于对齐数据，可选）
    data2_id_col: 表2的主键列（用于对齐数据，可选）
    db_connection: 数据库连接字符串（如果数据来自数据库）

    返回:
    bool: 两列内容是否完全相同
    dict: 详细的比较结果
    """

    def load_data(data):
        """加载数据，支持多种输入类型"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, str):
            # 如果是文件路径
            if data.endswith('.csv'):
                return pd.read_csv(data)
            elif data.endswith(('.xlsx', '.xls')):
                return pd.read_excel(data)
            elif db_connection:
                # 如果是数据库表名
                engine = create_engine(db_connection)
                return pd.read_sql(f"SELECT * FROM {data}", engine)
            else:
                raise ValueError("未提供数据库连接，无法读取数据库表")
        else:
            raise ValueError("不支持的数据类型")

    # 加载数据
    df1 = load_data(data1)
    df2 = load_data(data2)

    # 检查列是否存在
    if column_name not in df1.columns:
        raise ValueError(f"列 '{column_name}' 在 {data1_name} 中不存在")
    if column_name not in df2.columns:
        raise ValueError(f"列 '{column_name}' 在 {data2_name} 中不存在")

    # 提取要比较的列
    col1 = df1[column_name]
    col2 = df2[column_name]

    # 比较结果
    result = {
        'identical': False,
        'details': {
            f'{data1_name}_行数': len(col1),
            f'{data2_name}_行数': len(col2),
            '行数是否相同': len(col1) == len(col2),
            '唯一值数量是否相同': col1.nunique() == col2.nunique(),
            '值集合是否相同': set(col1.dropna().unique()) == set(col2.dropna().unique()),
            '是否有重复值差异': col1.duplicated().sum() != col2.duplicated().sum()
        }
    }

    # 详细比较
    if len(col1) == len(col2):
        # 如果行数相同，直接逐行比较
        result['details']['逐行完全相同'] = col1.equals(col2)

        # 如果提供了主键列，按主键对齐后比较
        if data1_id_col and data2_id_col:
            if data1_id_col in df1.columns and data2_id_col in df2.columns:
                merged = pd.merge(df1[[data1_id_col, column_name]],
                                  df2[[data2_id_col, column_name]],
                                  left_on=data1_id_col, right_on=data2_id_col,
                                  suffixes=('_1', '_2'))
                if not merged.empty:
                    aligned_identical = (merged[f'{column_name}_1'] == merged[f'{column_name}_2']).all()
                    result['details']['按主键对齐后完全相同'] = aligned_identical

    # 最终判断
    result['identical'] = (
            result['details']['行数是否相同'] and
            result['details'].get('逐行完全相同', False)
    )

    # 如果逐行比较为False，但值集合相同，说明只是顺序不同
    if not result['details'].get('逐行完全相同', True) and result['details']['值集合是否相同']:
        result['details']['仅顺序不同'] = True
        # 如果用户不关心顺序，可以认为相同
        result['identical'] = True

    return result['identical'], result


# 使用示例
if __name__ == "__main__":
    # 示例1: 比较两个DataFrame
    df1 = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    })

    df2 = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    })

    identical, details = compare_columns(df1, df2, 'name', '员工表1', '员工表2')
    print(f"列内容是否完全相同: {identical}")
    print("详细比较结果:")
    for key, value in details['details'].items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 50 + "\n")

    # 示例2: 比较顺序不同但内容相同的列
    df3 = pd.DataFrame({
        'id': [1, 2, 3, 4],
        'name': ['David', 'Charlie', 'Bob', 'Alice']  # 顺序不同
    })

    identical, details = compare_columns(df1, df3, 'name', '员工表1', '员工表3')
    print(f"列内容是否完全相同: {identical}")
    print("详细比较结果:")
    for key, value in details['details'].items():
        print(f"  {key}: {value}")