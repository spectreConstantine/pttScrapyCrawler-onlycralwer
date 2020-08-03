# --- The MIT License (MIT) Copyright (c) alvinconstantine(alvin.constantine@outlook.com), Mon Jul 13 15:28pm 2020 ---
import scrapy

class UptodatepttItem(scrapy.Item):
    _id = scrapy.Field() # 用文章超連結檔名摘取編碼成 12 碼的 mongoDB 的 ID
    p_index = scrapy.Field() # 在 pTT 裡的 index 頁碼
    p_author = scrapy.Field() # 作者ID識別
    p_comment = scrapy.Field() # 評論
    p_href = scrapy.Field() # 文章超連結檔名
    n_classify = scrapy.Field() # 分類
    n_subject = scrapy.Field() # 主題
    n_content = scrapy.Field() # 本文
    n_author = scrapy.Field() # 作者別名稱
    n_title = scrapy.Field() # 標題
    n_datime = scrapy.Field() # 日期 星期, 月, 日, 年 時間 時, 分, 秒
    r_content = scrapy.Field() # 本文內超連結
    a_ip = scrapy.Field()  # 發信站 IP
    a_country = scrapy.Field() # 發信站國家
    s_score = scrapy.Field() # 推噓文的計分摘要
    s_comment = scrapy.Field() # 推噓文的內文