# -*- coding: utf-8 -*-
"""
将浏览器复制的微博 Cookie 字符串转换为 Selenium 可用的 JSON 文件
"""

import json

# 1️⃣ 在这里粘贴你复制的 Cookie 字符串
cookie_str="XSRF-TOKEN=gnkcmztiSQisk8OmBfN1XP5N; SCF=AicuNMmbvXS7NAhb4xrL4OyJhYjM87Ww9RvUw7LH6SqTcqt0Yempv6ysEBWg3MarhnnWFGB2owkNv6iVcbcGGgA.; SUB=_2A25F1GQBDeRhGeFK41MT9SfMzDiIHXVmqPnJrDV8PUNbmtAbLUTVkW9NQuRm3RKWqWNtn-UG3QSd6w2Z9lRYVrfx; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFd6Eus12LMMdKUXuRi8Zzk5JpX5KzhUgL.FoMX1h2ESK.7S0B2dJLoIEq_i--ciKL8iK.fi--ciKLhiKnRi--Ri-2pi-i8i--Xi-iWiK.pTBtt; ALF=02_1761059153; WBPSESS=yvV4iXdcQ5w6shTHMljZDnWRDRV6sIVJNgxrhnQ3PUbZTGrdaaLP6k_0G893QWJVX3C7_j-bVh9VKgXLPENRSWGlI_u_VqoLNCrRjictpvVKCm95f0x75Ty6xhGFWfTKGQaeZexpOxxAxOZywJRyLw==; _s_tentry=weibo.com; Apache=6852909390350.004.1758467188421; SINAGLOBAL=6852909390350.004.1758467188421; ULV=1758467188424:1:1:1:6852909390350.004.1758467188421:"

# 2️⃣ 转换成列表字典
cookies = []
for item in cookie_str.strip().split(";"):
    if "=" not in item:
        continue
    name, value = item.strip().split("=", 1)
    cookies.append({
        "name": name,
        "value": value,
        "domain": ".weibo.com",
        "path": "/"
    })

# 3️⃣ 保存为 JSON 文件
with open("weibo_cookie.json", "w", encoding="utf-8") as f:
    json.dump(cookies, f, ensure_ascii=False, indent=2)

print(f"[SUCCESS] 已生成 weibo_cookie.json，包含 {len(cookies)} 个 Cookie")
