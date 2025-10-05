import pandas as pd
import os

def create_sample_excel_files():
    """
    Creates the 'data' directory and generates sample Excel files
    with predefined sheet names and data.
    """
    # Create the data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")
        print("Created directory: 'data'")

    # Sample data for all files
    data_map = {
        "bilibili.xlsx": {
            "plays": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "play_count": [50000000, 30000000, 10000000]
            }),
            "followers": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "followers": [1000000, 800000, 200000]
            }),
            "interactions": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "likes": [2500000, 1500000, 500000],
                "coins": [1800000, 1200000, 300000],
                "collections": [1600000, 1000000, 250000],
                "shares": [800000, 600000, 150000]
            }),
            "creations": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "creations": [1500, 1000, 300],
                "videos": [2000, 1500, 500]
            }),
            "comments": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "comments": [500000, 300000, 100000]
            }),
            "ratings": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "score": [9.5, 8.8, 7.2]
            })
        },
        "douban.xlsx": {
            "ratings": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "score": [9.2, 8.5, 6.5],
                "votes": [250000, 150000, 30000]
            }),
            "comments": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "comment_count": [80000, 50000, 10000]
            })
        },
        "imdb.xlsx": {
            "ratings": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "score": [8.8, 8.0, 7.0],
                "votes": [120000, 80000, 15000]
            }),
            "rank": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "rank": [5, 15, 50]
            })
        },
        "tencent.xlsx": {
            "plays": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "tencent_plays": [80000000, 45000000, 20000000]
            })
        },
        "youku.xlsx": {
            "plays": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "youku_plays": [60000000, 35000000, 15000000]
            })
        },
        "guduo.xlsx": {
            "plays": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "guduo_plays": [1000000, 700000, 250000]
            })
        },
        "baidu_index.xlsx": {
            "index": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "baidu_index": [80000, 50000, 15000]
            })
        },
        "douyin.xlsx": {
            "creations": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "likes": [200000, 100000, 30000],
                "comments": [15000, 8000, 2000],
                "shares": [8000, 5000, 1000]
            })
        },
        "weibo.xlsx": {
            "discussions": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "posts": [150000, 80000, 20000]
            })
        },
        "tieba.xlsx": {
            "stats": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "posts": [12000, 6000, 1500],
                "followers": [80000, 50000, 10000]
            })
        },
        "taobao_xianyu.xlsx": {
            "sales": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "taobao": [50000, 20000, 3000],
                "xianyu": [15000, 5000, 500]
            })
        },
        "industry.xlsx": {
            "games": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "games": [3, 1, 0]
            }),
            "shows": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "shows": [5, 2, 0]
            }),
            "original_works": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "original_works": [10, 5, 1]
            }),
            "patents": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "patents": [2, 0, 0]
            })
        },
        "risk.xlsx": {
            "risk": pd.DataFrame({
                "anime": ["番剧A", "番剧B", "番剧C"],
                "douban_score": [9.2, 8.5, 6.5],
                "negative_ratio": [0.05, 0.1, 0.45]
            })
        }
    }

    # Write data to Excel files
    for filename, sheets in data_map.items():
        filepath = os.path.join("data", filename)
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"Successfully created: {filepath}")

if __name__ == "__main__":
    create_sample_excel_files()