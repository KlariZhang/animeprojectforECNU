

# -*- coding: utf-8 -*-
"""
合并版：从 Excel 读取 sheet1.anime 并抓取百度指数，固定时间 2023-07-01 ~ 2025-06-30
"""

import requests
from requests.exceptions import RequestException
import json
import time
import datetime
import pandas as pd
import random
from pathlib import Path

# ======================== 用户配置区 ========================
CREDENTIALS = {
    # 请在下面粘贴你的 BDUSS 值
    "cookie_BDUSS": "Uk3d0xWM2E5aElZdDl1T21XRUZVYnc5M1lBTVVmSzRKRkJ1bnl4NmhQUmwzNHBvSVFBQUFBJCQAAAAAAQAAAAEAAAC-qKdJRWdnZ2dnZzcxMUtyaWEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGVSY2hlUmNoe",
    # 请在下面粘贴你的 Cipher-Text 值
    "cipherText": "1754798782305_1754838864758_T2jaZxeYskl5oMREey6MkQuEj1es/+ZucNthIxmSc1sFJzcBt04u9NJL2KGga5OoLzFBa/Kb2lsUtHGK3tYVDA3rNw1pnatSdFTirjCaYVwxBxdy69PKjFlp8MtBhtihEv0DeHwQvUiuIfsrmjrzvqEtKBYRy+vtwBdtKMaXEuv9KBNtH36Fqi80IpqwUVfXah8osNuEi9xJzHvqvqCjNwfKNMXKGWnCcm4iA6gRFqkBdW6oFmGbLQgdOF51OjNh5lSmzdI5quLKwhFHP22GT4Q/CvSfaRFCs56vp3uBb64MLmkl7V24yPO0xDyX9Hot3Ca/5KiyAf3L19qnqCKorMITBaZakenzupbOsQRb9WLHDREj2/PiO+U1lZvhRMCCspcqXO/mIcmnsiE8A9U06s0aDdfHzDD9J+oIEQaOil2zyAoIfNfSFCWBbFogDi1mKBQr8yhyGo8CQq34Hr7hTA==",
}

REGION_CODE = 0  # 0=全国，其它地区请按百度指数地区编码设置
EXCEL_PATH = "newall_cleaned.xlsx"   # 你的 Excel 文件
SHEET_NAME = "movie"
COLUMN_NAME = "anime"
GROUP_MODE = "separate"     # 'separate'：每个词独立成组；'together'：把所有词放一组做对比

START_DATE = "2023-07-01"
END_DATE   = "2025-06-30"
# ==========================================================


def generate_http_headers(credential):
    # 根据凭证生成请求头
    return {
        "Cookie": "BDUSS=" + credential["cookie_BDUSS"],
        "Cipher-Text": credential["cipherText"],
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://index.baidu.com/v2/main/index.html",
        "Host": "index.baidu.com",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/103.0.0.0 Safari/537.36"
        ),
    }


def decrypt(ptbk, index_data):
    # 数据解密函数
    n = len(ptbk) // 2
    a = dict(zip(ptbk[:n], ptbk[n:]))
    return "".join([a[s] for s in index_data])


def format_keywords_for_api(keywords):
    """
    将关键词列表格式化为 API 所需 JSON:
    输入: list[list[str]] 形如 [['海贼王'], ['火影忍者','死神']]
    输出: JSON 字符串
    """
    converted = [[{"name": keyword, "wordType": 1} for keyword in sublist] for sublist in keywords]
    return json.dumps(converted, ensure_ascii=False)




import json
import time
import random
import pandas as pd
import datetime
from urllib.parse import quote
from requests.exceptions import RequestException

def chunked(seq, size):
    """把序列按固定大小切块"""
    for i in range(0, len(seq), size):
        yield seq[i:i+size]

def get_baidu_index(keywords, start_date, end_date, region_code, credential,
                    batch_size=5, pause=(0.8, 1.6), max_retries=3):
    """
    分批抓取百度指数并纵向对齐返回 DataFrame：
    - keywords: list[list[str]]  外层每个元素是一组（你现在每组只有一个词）
    - batch_size: 每批提交多少“组”（建议 3~8）
    """
    http_headers = generate_http_headers(credential)

    all_frames = []
    total = len(keywords)
    done = 0

    for batch_id, batch in enumerate(chunked(keywords, batch_size), start=1):
        print(f"[Batch {batch_id}] groups {done+1}..{min(done+len(batch), total)} / {total}")

        # 组装参数
        word_for_check = ",".join(["+".join(kw_group) for kw_group in batch])
        word_for_api_json = format_keywords_for_api(batch)
        word_for_api = quote(word_for_api_json, safe="")  # URL 编码很重要

        # === 1)（可选）逐批校验关键词存在性 ===
        try:
            check_url = f"https://index.baidu.com/api/AddWordApi/checkWordsExists?word={quote(word_for_check)}"
            r = requests.get(check_url, headers=http_headers, timeout=10)
            if r.status_code != 200:
                print(f"  [check] HTTP {r.status_code}, body[:120]={r.text[:120]!r}")
            else:
                j = r.json()
                invalid = j.get("data", {}).get("result") or []
                if invalid:
                    print(f"  [check] 无效关键词: {[i.get('word') for i in invalid]}")
                    # 直接跳过这批里无效的词
                    valid_batch = [[w for w in g if w not in {i.get('word') for i in invalid}] for g in batch]
                    valid_batch = [g for g in valid_batch if g]
                    if not valid_batch:
                        done += len(batch)
                        continue
                    # 重新准备 URL 参数
                    word_for_api_json = format_keywords_for_api(valid_batch)
                    word_for_api = quote(word_for_api_json, safe="")
        except Exception as e:
            print(f"  [check] 跳过校验（解析失败）：{e}")

        # === 2) 拉取数据（带重试与可读报错）===
        for attempt in range(1, max_retries+1):
            try:
                index_url = (
                    f"https://index.baidu.com/api/SearchApi/index?"
                    f"area={region_code}&word={word_for_api}&startDate={start_date}&endDate={end_date}"
                )
                resp = requests.get(index_url, headers=http_headers, timeout=15)

                if resp.status_code != 200:
                    print(f"  [index] HTTP {resp.status_code}, body[:200]={resp.text[:200]!r}")
                    raise RequestException(f"HTTP {resp.status_code}")

                data_j = resp.json()
                data = data_j.get("data")
                if not data or "uniqid" not in data:
                    print(f"  [index] 返回缺少 data/uniqid，body[:200]={resp.text[:200]!r}")
                    raise ValueError("missing uniqid")

                uniqid = data["uniqid"]

                # 取解密 key
                ptbk_url = f"https://index.baidu.com/Interface/ptbk?uniqid={uniqid}"
                ptbk_resp = requests.get(ptbk_url, headers=http_headers, timeout=10)
                if ptbk_resp.status_code != 200:
                    print(f"  [ptbk] HTTP {ptbk_resp.status_code}, body[:120]={ptbk_resp.text[:120]!r}")
                    raise RequestException(f"PTBK HTTP {ptbk_resp.status_code}")
                ptbk = ptbk_resp.json().get("data")
                if not ptbk:
                    print(f"  [ptbk] 无 data，body[:200]={ptbk_resp.text[:200]!r}")
                    raise ValueError("missing ptbk data")

                # 解密每个词的序列
                series_map = {}
                for item in data.get("userIndexes", []):
                    keyname = ",".join([w["name"] for w in item["word"]])
                    enc = item["all"]["data"]
                    dec_str = decrypt(ptbk, enc)
                    vals = [int(x) if x else 0 for x in dec_str.split(",")]

                    # 按日或按周建索引
                    days_span = (datetime.datetime.strptime(end_date, "%Y-%m-%d")
                                 - datetime.datetime.strptime(start_date, "%Y-%m-%d")).days
                    if days_span > 365 and len(vals) < days_span:
                        idx = pd.date_range(start=start_date, periods=len(vals), freq="W")
                    else:
                        idx = pd.date_range(start=start_date, periods=len(vals), freq="D")
                    series_map[keyname] = pd.Series(vals, index=idx)

                if not series_map:
                    print("  [index] 本批次无可用数据。")
                    break

                frame = pd.DataFrame(series_map)
                all_frames.append(frame)
                print(f"  [ok] 本批次 {frame.shape[1]} 列，{frame.shape[0]} 行")
                break  # 成功，跳出重试

            except Exception as e:
                print(f"  [retry {attempt}/{max_retries}] {e}")
                if attempt == max_retries:
                    print("  [giveup] 放弃本批次。")
                time.sleep(random.uniform(*pause))

        done += len(batch)
        time.sleep(random.uniform(*pause))  # 批间隔，降低风控

    if not all_frames:
        print("未获取到任何数据。")
        return None

    # 对齐所有批次（日期为并集，列为并集）
    result = pd.concat(all_frames, axis=1).sort_index()
    print(f"查询完成：总计 {result.shape[1]} 列，{result.shape[0]} 行")
    return result






def load_keywords_from_excel(path, sheet_name="sheet1", column="anime", group_mode="separate"):
    """
    从 Excel 读取关键词为脚本所需结构(list[list[str]])。
    - group_mode='separate'：每个词单独成组（常用）
    - group_mode='together'：把所有词放一组（做多词对比）
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"未找到 Excel：{path.resolve()}")

    df = pd.read_excel(path, sheet_name=sheet_name)
    names = (
        df[column]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )
    if not names:
        raise ValueError(f"在 {path.name} 的 {sheet_name}.{column} 列未读取到任何关键词")

    return [names] if group_mode == "together" else [[n] for n in names]


if __name__ == "__main__":
    # 1) 读取 Excel 的 sheet1.anime
    keywords_groups = load_keywords_from_excel(EXCEL_PATH, SHEET_NAME, COLUMN_NAME, GROUP_MODE)

    start_date = START_DATE
    end_date = END_DATE

    all_frames = []

    # 逐一处理每个关键词组（通常每个词单独一组）
    for i, group in enumerate(keywords_groups, start=1):
        print(f"=== 查询第 {i}/{len(keywords_groups)} 个关键词: {group} ===")
        df_single = get_baidu_index([group], start_date, end_date, REGION_CODE, CREDENTIALS,
                                    batch_size=1)  # batch_size=1 保证每次只抓一个

        # 如果抓取失败或无数据，生成空列
        if df_single is None or df_single.empty:
            import pandas as pd
            idx = pd.date_range(start=start_date, end=end_date, freq='D')
            df_single = pd.DataFrame({",".join(group): [None]*len(idx)}, index=idx)

        all_frames.append(df_single)

        # 间隔，降低风控
        import random, time
        time.sleep(random.uniform(0.8, 1.6))

    # 合并所有关键词的数据（按原顺序）
    if all_frames:
        df_all = pd.concat(all_frames, axis=1)  # 保持原顺序
        out_name = f"baidu_movie_{start_date}_to_{end_date}_new.csv"
        df_all.to_csv(out_name, index=True, encoding="utf-8-sig")
        print(f"\n所有关键词数据已合并保存到文件: {out_name}")
        print("\n--- 数据预览 ---")
        print(df_all.head())
    else:
        print("未获取到任何数据。")



