# --- The MIT License (MIT) Copyright (c) alvinconstantine(alvin.constantine@outlook.com), Mon Jul 13 15:28pm 2020 ---
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.linkextractors import re
from datetime import datetime
from scrapy.exceptions import CloseSpider

process = CrawlerProcess(get_project_settings())
process.crawl('getuptodatePtt') 
process.start() # the script will block here until the crawling is finished
