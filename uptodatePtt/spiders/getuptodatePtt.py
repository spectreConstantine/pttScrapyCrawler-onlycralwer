# --- The MIT License (MIT) Copyright (c) alvinconstantine(alvin.constantine@outlook.com), Mon Jul 13 15:28pm 2020 uptodatePtt_v9.7-4 ---
import scrapy
from datetime import datetime
from uptodatePtt.items import UptodatepttItem
from scrapy.linkextractors import re
from scrapy.exceptions import CloseSpider
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

class GetuptodatepttSpider(scrapy.Spider):
    name = 'getuptodatePtt'

    def __init__(self, board_name=None, page_num=None, *args, **kwargs):
        super(GetuptodatepttSpider, self).__init__(*args, **kwargs)
        self.pttRooturl = 'www.ptt.cc'
        self.pptPrefix = 'bbs'
        self.pttStartPage = 'index.html'
        self.pttCookies = {
        	'over18': '1'
        	}     	
        self.abbrMonnum = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        self.abbrWeeknum = {'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, 'Sat': 6, 'Sun': 0}			
        if board_name:
            self.boardName = board_name
        else:
            self.log('參數錯誤，未指定板名或不正確的板名。請指定 board_name 板名! 範例語法及參數: scrapy crawl getuptodatePtt -a board_name=Gossiping -a page_num=0')
            self.boardName = 'Python'
        self.log('使用板名: %s' % self.boardName)
        self.startUrl = f'https://{self.pttRooturl}/{self.pptPrefix}/{self.boardName}/{self.pttStartPage}'              
        if page_num and int(page_num) > 0:
            self.pageNum = int(page_num)
        else:
            self.pageNum = 0
            self.log('未指定頁數或不正確的頁數，目前設定為 0，即首頁單頁。\n請使用參數: scrapy crawl getuptodatePtt -a page_num=0')
        self.log('目前的起始網址為:%s' % self.startUrl)

    def start_requests(self):
        cbKwargs = {}
        cbKwargs['board_name'] = { 
        	'boardName' : self.boardName,
            'bbsUrl' : self.startUrl,
        	}
        self.logger.info(f'進行[ %s ] 板...' % cbKwargs['board_name']['boardName'])
        yield scrapy.Request(url=cbKwargs['board_name']['bbsUrl'], cookies=self.pttCookies, callback=self.prase, cb_kwargs=cbKwargs)        

    def prase(self, response, board_name):

        def getIndex(response):
            p_navigation = {}
            actionbar_btns = response.css('.btn-group-paging') # 選擇器 # 最舊,‹ 上頁,下頁 ›,最新
            if actionbar_btns:
                for btn_ in actionbar_btns.css('a'):
                    if not 'disabled' in btn_.get():
                        p_navigation[btn_.css('a::text').get().lstrip('‹ ').rstrip(' ›')] = btn_.css('a').attrib['href'].split('/')[-1]
                    else:
                        p_navigation[btn_.css('a::text').get().lstrip('‹ ').rstrip(' ›')] = ''
            if p_navigation['上頁']:
                navigation_previous_page = p_navigation['上頁']
                response_index = int(navigation_previous_page.replace('.html', '').replace('index', '')) + 1 #上一頁的網址中index的字串轉數字 + 1
            else:
                response_index = int(response.url.split('/')[-1].replace('.html', '').replace('index', ''))
            return response_index

        def getArticles(response):
            href_ids = {}
            rlist_container = response.xpath('//*[@class="r-list-sep"]|//*[@class="r-ent"]')  # 選擇器 # 文章列表
            listsep_flag = 'r-list-sep' in rlist_container.css('div::attr(class)').getall()
            if rlist_container and listsep_flag:
                for i, rlist in enumerate(rlist_container):
                    if rlist.css('div::attr(class)').get() == 'r-list-sep':                
                        if i > 0:
                            for j in range(i-1, -1, -1):
                                p_title = rlist_container[j].css('.title>a::text').get() # 標題
                                if p_title and not '公告' in p_title:              
                                    p_href = rlist_container[j].css('.title>a').attrib['href'] # 文章超連結                    
                                    if p_href:                                
                                        href_id = p_href.split('/')[-1].replace('.html', '')
                                        href_ids[href_id] = p_title  # 裡面的值是另一個字典 { '文章的 href link 為 key': '文章的 title 為值' }, 例如: { 'M.1574522529.A.F8F': '[問卦] 我想到'}                                        
                        break
            elif rlist_container:
                for rlist in rlist_container:
                        p_title = rlist.css('.title>a::text').get() # 標題
                        if p_title and not '公告' in p_title:              
                            p_href = rlist.css('.title>a').attrib['href'] # 文章超連結                    
                            if p_href:                                
                                href_id = p_href.split('/')[-1].replace('.html', '')
                                href_ids[href_id] = p_title  # 裡面的值是另一個字典 { '文章的 href link 為 key': '文章的 title 為值' }, 例如: { 'M.1574522529.A.F8F': '[問卦] 我想到'}
            return href_ids  

        def getContent(response, p_title):

            def content_shrink(s_content):
                try:
                    s_content = re.sub(r'(Sent from (\w+ ?)+)|(Sent from JPTT on my iPhone)|(Sent from JPTT on my iPad)|(Sent from my (\w+ ?)+)|(Sent from \w+ on my (\w+ ?)+)|(/cdn-cgi/l/email-protection)', '', s_content) # 文章本文移除無意義的內容
                    #s_content = re.sub(r'(QAQ)|(Orz)|(orz)|(xd+)|(QQ)|(qq)|(XD+)|(0\.0)|(\^_\^.?)|(-+)|(:\))|(：）)|(\.\n)|(\.\.+)|(=///=)|(m\(_ _\)m)|(=\s)+|[▲○★／」】【「）（＞。,，、；～~！!？|\?\*]\s?', ' ', s_content) # 文章本文移除多餘的內容
                    s_content = re.sub(r'[\s]+', ' ', s_content) # 文章本文移除多餘的空白
                    s_content = s_content.strip() # 文章本文移除左邊多餘的空白
                except Exception as e:
                    print(f'exception occurs: {e}')
                finally:
                    return s_content
            
            article = {} # 本文清單字典
            main_article_selector = response.xpath('//*[@id="main-content"]') # 文章主文選擇器
            article_lists = main_article_selector.xpath('./text()|./a/@href|span[has-class("hl")]/text()').getall() # 文章列表
            article['r_content'] = [] # 本文內的超連結清單
            n_content = '' # 本文
            n_count = 0 # 本文內超連結的數量
            p_author, n_author, name_fetch = '', '', ''
            for n_ in article_lists:
                if n_[:8] == 'https://' or n_[:7] == 'http://':
                    article['r_content'].append(n_) # 本文內超連結
                    n_content += '{_'+str(n_count)+'}' # 本文內其他的超連結以 {_n} 代替
                    n_count += 1 # 將 {_n} 的數字依續加1
                else:  # 本文內其他非超連結即為文字
                        if re.search(r'作者: \w+ \(.+\) ', n_):
                            if not name_fetch:
                                name_fetch = re.search(r'作者: \w+ \(.+\) ', n_).group()
                                n_ = n_.replace(name_fetch,'')
                        n_content += n_   # 將文字依續累加
            if article['r_content'] == []:
                del article['r_content']
            article['n_content'] = content_shrink(n_content) # 移除文章多餘的內容
            nick_name = main_article_selector.xpath('//span[text()="作者"]/following-sibling::span/text()').get() # 作者
            if not nick_name:
                nick_name = main_article_selector.xpath('//span[text()=" 作者 "]/following-sibling::span/text()').get()
            if nick_name:
                nick_name = nick_name.strip()
            elif name_fetch:
                nick_name = name_fetch[name_fetch.index(' ')+1:-1]
            else:
                nick_name = ''
            if '(' in nick_name:
                try:
                    p_author = nick_name[:nick_name.index('(')-1].rstrip()
                    n_author = nick_name[nick_name.index('(')+1:len(nick_name)-1]
                except ValueError:
                    try:
                        p_author, n_author = nick_name.replace('  ', ' ').split(' ')
                        n_author = n_author.lstrip('(').rstrip(')')
                    except ValueError:
                        try:
                            p_author = nick_name[:nick_name.index(' ')-1]
                            n_author = nick_name[nick_name.index(' ')+1:]
                        except ValueError:
                            p_author = nick_name
                            n_author = ''
            if p_author:
                article['p_author'] = p_author
            if n_author:
                article['n_author'] = n_author
            n_title = main_article_selector.xpath('//span[text()="標題"]/following-sibling::span/text()').get()  # 標題
            if not n_title:
                n_title = p_title
            article['n_title'] = n_title
            try:
                n_classify = n_title[n_title.index('[')+1:n_title.index(']')]
                n_subject = n_title[n_title.index(']')+1:]
            except ValueError:
                try:
                    n_title.index('[')
                except ValueError:
                    n_classify = '無標'
                    n_subject = n_title
                else:
                    n_classify = n_title[1:3]
                    n_subject = n_title[4:]
            article['n_classify'] = n_classify.lstrip() # 分類
            article['n_subject'] = content_shrink(n_subject.lstrip()) # 主題
            n_dtstr = main_article_selector.xpath('//span[text()="時間"]/following-sibling::span/text()').get()  # 星期, 月份, 日, 時間和日期
            if n_dtstr:  # 確定有此星期, 月份, 日, 時間和日期欄位
                try:
                    check_d = n_dtstr.replace('  ', ' ').split(' ')
                    check0 = self.abbrWeeknum[check_d[0]]
                    check1 = self.abbrMonnum[check_d[1]]
                    check2 = int(check_d[2])
                    check3 = check_d[3].index(':')
                    check4 = int(check_d[4])
                    check_t  = [ int(i) for i in check_d [3].split(':') ] 
                    n_datime = datetime(check4, check1, check2, check_t[0] , check_t[1], check_t[2]) # strftime("%a %b %d %H:%M:%S %Y") / ("%a %b %d %H:%M:%S %Y")
                except:
                    n_datime = ''
            else:
                n_datime = ''
            article['n_datime'] = n_datime  # 格式化為ISODate年月日時分秒 格式為  '2019-11-22T11:04:56'
            ip_country = main_article_selector.css('.f2::text').getall()
            for ip_c in ip_country:
                if re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', ip_c):
                    a_ip = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', ip_c).group() # 發信站 IP
                    article['a_ip'] = a_ip
                    try:
                        ip_cMinusa_ip = ip_c[ip_c.index(a_ip) + len(a_ip):]
                        if '臺灣' in ip_cMinusa_ip:
                            article['a_country'] = '臺灣'
                        elif re.search(r'[\u4e00-\u9fff]+', ip_cMinusa_ip):
                            a_country = re.search(r'[\u4e00-\u9fff]+', ip_cMinusa_ip).group() # 發信站國家
                            article['a_country'] = a_country
                    except IndexError:
                        pass
                    break
            all_comments = main_article_selector.css('.push') #所有的推噓文
            if all_comments:
                article['p_comment'] = []
                article['s_comment'] = {}
                article['s_score'] = 0
                _score, _push, _boo, _neutral = 0, 0, 0, 0
                for comment in all_comments:
                    p_comment = {}
                    c_userid = comment.css('.push>.push-userid::text').get() # 推噓者
                    if not c_userid:
                        continue                 
                    else:               
                        c_userid = c_userid.rstrip()
                        p_comment[c_userid] = {}
                        c_content = comment.css('.push>.push-content::text').get() # 推噓內文
                        if c_content:
                            c_content = c_content.lstrip(': ')
                        else:
                            c_content = ''                
                        p_comment[c_userid]['c_content'] = content_shrink(c_content)  # 修飾推噓內文
                        push_ipdatetime = comment.css('.push>.push-ipdatetime::text').get() # 取得推噓者的IP,日期及時間
                        if push_ipdatetime.replace('\n', ''):
                            c_date, c_time = '', ''
                            if re.search(r'[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', push_ipdatetime):
                                p_comment[c_userid]['c_ip'] =  re.search(r'[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', push_ipdatetime).group() # 推噓者的IP
                            if re.search(r'[0-9]+/[0-9]+', push_ipdatetime):
                                c_date = re.search(r'[0-9]+/[0-9]+', push_ipdatetime).group() # 推噓的日期
                                c_date = c_date[:5]
                                c_date0, c_date1 = c_date.split('/')
                                if int(c_date0) > 12 or int(c_date0) <1:
                                    c_date0 = str(10)
                                if int(c_date1) > 31 or int(c_date1) <1 or (int(c_date1) == 29 and int(c_date0) == 2):
                                    c_date1 = str(10)
                                c_date = f'{c_date0}/{c_date1}'                        
                            if re.search(r'[0-9]+:[0-9]+', push_ipdatetime):
                                c_time = re.search(r'[0-9]+:[0-9]+', push_ipdatetime).group() # 推噓的時間
                                c_time = c_time[:5]
                                c_time0, c_time1 = c_time.split(':')
                                if int(c_time0) > 24 or int(c_time0) < 1:
                                    c_time0 = str(10)
                                if int(c_time1) > 60 or int(c_time1) < 1:
                                    c_time1 = str(10)
                                c_time = f'{c_time0}:{c_time1}'                        
                            if c_date and c_time:
                                try:
                                    p_comment[c_userid]['c_datime'] = datetime.strptime(f'{int(n_dtstr[-4:])}/{c_date} {c_time}', "%Y/%m/%d %H:%M")
                                except:
                                    p_comment[c_userid]['c_datime'] = ''
                            c_tag = comment.css('.push>.push-tag::text').get() #推或噓的標籤
                            if c_tag:
                                c_tag = c_tag.rstrip()
                                if c_tag == '推':
                                    p_comment[c_userid]['c_tag'] = 1 # 推 為 正1
                                    _push += 1
                                    _score += 1
                                elif c_tag == '噓':
                                    p_comment[c_userid]['c_tag'] = -1 # 噓 為 負1
                                    _boo += 1
                                    _score -= 1
                                else:
                                    p_comment[c_userid]['c_tag'] = 0 # 箭頭 為 0
                                    _neutral += 1
                            article['p_comment'].append(p_comment) # 推噓文的列表
                article['s_score'] = _score
                article['s_comment'] = {
                    'count' : len(all_comments),
                    'push' : _push,
                    'boo' : _boo,
                    'neutral' : _neutral,
                    } # 推噓文的分數列表
            return article

        def prase_errback(failure):
            self.logger.error(repr(failure))
            if failure.check(HttpError):
                response = failure.value.response
                self.logger.error(f'錯誤[HttpError]_網址[{response.url}]')
            elif failure.check(DNSLookupError):
                request = failure.request
                self.logger.error(f'錯誤[DNSLookupError]_網址[{request.url}]')
            elif failure.check(TimeoutError, TCPTimedOutError):
                request = failure.request
                self.logger.error(f'錯誤[TimeoutError]_網址[{request.url}]')

        def serialize_boardArticles(response, current_index, p_title):
            # self.logger.info(f'網頁[{response.url}]成功回應<serialize>')
            article = getContent(response, p_title)
            article['p_index'] = current_index
            p_href = response.url.split('/')[-1]
            article['p_href'] = p_href
            phref_id = p_href.replace('.','')
            article['_id'] = phref_id[2:11] + phref_id[12:15]
            pttItem = UptodatepttItem(article)            
            yield pttItem

        def parse_follow(response, current_index):
            # self.logger.info(f'網頁[{response.url}]成功回應<follow>')   
            articleHrefs = getArticles(response)
            for current_article in articleHrefs.keys():
                parsecbkwargs['current_index'] = current_index
                parsecbkwargs['p_title'] = articleHrefs[current_article]
                yield scrapy.Request(url=f'{self.startUrl.replace("index.html", f"{current_article}.html")}', cookies=self.pttCookies, callback=serialize_boardArticles, errback=prase_errback, cb_kwargs=parsecbkwargs)

        self.logger.info(f'網頁[{response.url}]成功回應<parse>')
        parsecbkwargs = {}
        responseIndex = getIndex(response) # --- 檢查項目(2) response_index 是否相同
        lastpageIndex = responseIndex - self.pageNum
        pages_Delta = responseIndex - lastpageIndex
        accumulatedHrefs = getArticles(response) # --- 檢查項目(3) 持續抓取首頁開始的所有的文章 超連結 href 直到上次的頁面
        boardLastIndexHrefs = sorted([hrefs for hrefs in accumulatedHrefs.keys()])
        last_article_title = accumulatedHrefs[boardLastIndexHrefs[-1]]
        for current_article in accumulatedHrefs.keys():
            parsecbkwargs['current_index'] = responseIndex
            parsecbkwargs['p_title'] = accumulatedHrefs[current_article]
            yield scrapy.Request(url=self.startUrl.replace("index.html", "%s.html" % current_article), cookies=self.pttCookies, callback=serialize_boardArticles, errback=prase_errback, cb_kwargs=parsecbkwargs)
        if pages_Delta > 0:
            followcbkwargs = {} 
            for current_index in range(responseIndex-1, lastpageIndex-1, -1):
                self.logger.info('往[ %s ]板_下頁[ %d ]' % (board_name['boardName'], current_index))
                followcbkwargs['current_index'] = current_index
                yield scrapy.Request(url=self.startUrl.replace(".html", "%s.html" % current_index), cookies=self.pttCookies, callback=parse_follow, errback=prase_errback, cb_kwargs=followcbkwargs) 