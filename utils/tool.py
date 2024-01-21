#!/usr/bin/env python
# encoding: utf-8
# Author: Anton Chen <contact@antonchen.com>
import asyncio
import aiohttp
import os
import time
import hashlib
import re
from utils import config

# GET 请求
# 多线程处理
# 超时时间 3 秒
# 非 200 状态码重试 3 次
# 返回订阅内容
async def fetch(session, url):
    retry_count = 5
    timeout = aiohttp.ClientTimeout(total=3)
    for _ in range(retry_count):
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            pass
    return None

# 写入缓存
def write_cache(cache_file, content):
    with open(cache_file, 'w') as f:
        f.write(content)

async def cached_multi_threaded_get(urls):
    # 缓存时间 8 小时
    # 缓存文件在当前 cache 目录下
    # 文件名为 url 的 md5 值
    cache = {}
    cache_dir = config.CACHE_DIR
    # 初始化缓存目录
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    async with aiohttp.ClientSession() as session:
        for url in urls:
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_file = cache_dir + url_hash
            if os.path.exists(cache_file):
                if time.time() - os.path.getmtime(cache_file) < config.CACHE_EXPIRE:
                    with open(cache_file, 'r') as f:
                        cache[url_hash] = f.read()
                else:
                    cache[url_hash] = await fetch(session, url)
                    if cache[url_hash]:
                        write_cache(cache_file, cache[url_hash])
            else:
                cache[url_hash] = await fetch(session, url)
                if cache[url_hash]:
                    write_cache(cache_file, cache[url_hash])
    return cache.values()


def is_ip(string):
    """判断字符串是否是IP地址"""
    pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+$')
    return bool(pattern.search(string))

regex_patterns = {
    'HK': re.compile('香港|沪港|呼港|中港|HKT|HKBN|HGC|WTT|CMI|穗港|广港|京港|🇭🇰|HK|Hongkong|Hong Kong|HongKong|HONG KONG'),
    'TW': re.compile('台湾|台灣|臺灣|台北|台中|新北|彰化|台|CHT|HINET|TW|Taiwan|TAIWAN'),
    'MO': re.compile('澳门|澳門|(\\s|-)?MO\\d*|CTM|MAC|Macao|Macau'),
    'SG': re.compile('新加坡|狮城|獅城|沪新|京新|泉新|穗新|深新|杭新|广新|廣新|滬新|SG|Singapore|SINGAPORE'),
    'JP': re.compile('日本|东京|大阪|埼玉|京日|苏日|沪日|广日|上日|穗日|川日|中日|泉日|杭日|深日|JP|Japan|JAPAN'),
    'US': re.compile('美国|美國|京美|硅谷|凤凰城|洛杉矶|西雅图|圣何塞|芝加哥|哥伦布|纽约|广美|(\\s|-)?(?<![AR])US\\d*|USA|America|United States'),
    'KR': re.compile('韩国|韓國|首尔|韩|韓|春川|KOR|KR|Kr|(?<!North\\s)Korea'),
    'KP': re.compile('朝鲜|KP|North Korea'),
    'RU': re.compile('俄罗斯|俄羅斯|毛子|俄国|RU|RUS|Russia'),
    'IN': re.compile('印度|孟买|\\bIN|IND|India|INDIA|Mumbai'),
    'ID': re.compile('印尼|印度尼西亚|雅加达|ID|IDN|Indonesia'),
    'GB': re.compile('英国|英國|伦敦|UK|England|United Kingdom|Britain'),
    'DE': re.compile('德国|德國|法兰克福|(\\s|-)?DE\\d*|(\\s|-)?GER\\d*|🇩🇪|German|GERMAN'),
    'FR': re.compile('法国|法國|巴黎|FR(?!EE)|France'),
    'DK': re.compile('丹麦|丹麥|DK|DNK|Denmark'),
    'NO': re.compile('挪威|(\\s|-)?NO\\d*|Norway'),
    'IT': re.compile('意大利|義大利|米兰|(\\s|-)?IT\\d*|Italy|Nachash'),
    'VA': re.compile('梵蒂冈|梵蒂岡|(\\s|-)?VA\\d*|Vatican City'),
    'BE': re.compile('比利时|比利時|(\\s|-)?BE\\d*|Belgium'),
    'AU': re.compile('澳大利亚|澳洲|墨尔本|悉尼|(\\s|-)?AU\\d*|Australia|Sydney'),
    'CA': re.compile('加拿大|蒙特利尔|温哥华|多伦多|滑铁卢|楓葉|枫叶|CA|CAN|Waterloo|Canada|CANADA'),
    'MY': re.compile('马来西亚|马来|馬來|MY|Malaysia|MALAYSIA'),
    'MV': re.compile('马尔代夫|馬爾代夫|(\\s|-)?MV\\d*|Maldives'),
    'TR': re.compile('土耳其|伊斯坦布尔|(\\s|-)?TR\\d|TR_|TUR|Turkey'),
    'PH': re.compile('菲律宾|菲律賓|(\\s|-)?PH\\d*|Philippines'),
    'TH': re.compile('泰国|泰國|曼谷|(\\s|-)?TH\\d*|Thailand'),
    'VN': re.compile('越南|胡志明市|(\\s|-)?VN\\d*|Vietnam'),
    'KH': re.compile('柬埔寨|(\\s|-)?KH\\d*|Cambodia'),
    'LA': re.compile('老挝|(\\s|-)(?<!RE)?LA\\d*|Laos'),
    'BD': re.compile('孟加拉|(\\s|-)?BD\\d*|Bengal'),
    'MM': re.compile('缅甸|緬甸|(\\s|-)?MM\\d*|Myanmar'),
    'LB': re.compile('黎巴嫩|(\\s|-)?LB\\d*|Lebanon'),
    'UA': re.compile('乌克兰|烏克蘭|(\\s|-)?UA\\d*|Ukraine'),
    'HU': re.compile('匈牙利|(\\s|-)?HU\\d*|Hungary'),
    'CH': re.compile('瑞士|苏黎世|(\\s|-)?CH\\d*|Switzerland'),
    'SE': re.compile('瑞典|SE|Sweden'),
    'LU': re.compile('卢森堡|(\\s|-)?LU\\d*|Luxembourg'),
    'AT': re.compile('奥地利|奧地利|维也纳|(\\s|-)?AT\\d*|Austria'),
    'CZ': re.compile('捷克|(\\s|-)?CZ\\d*|Czechia'),
    'GR': re.compile('希腊|希臘|(\\s|-)?GR(?!PC)\\d*|Greece'),
    'IS': re.compile('冰岛|冰島|(\\s|-)?IS\\d*|ISL|Iceland'),
    'NZ': re.compile('新西兰|新西蘭|(\\s|-)?NZ\\d*|New Zealand'),
    'IE': re.compile('爱尔兰|愛爾蘭|都柏林|(\\s|-)?IE(?!PL)\\d*|Ireland|IRELAND'),
    'IM': re.compile('马恩岛|馬恩島|(\\s|-)?IM\\d*|Mannin|Isle of Man'),
    'LT': re.compile('立陶宛|(\\s|-)?LT\\d*|Lithuania'),
    'FI': re.compile('芬兰|芬蘭|赫尔辛基|(\\s|-)?FI\\d*|Finland'),
    'AR': re.compile('阿根廷|(\\s|-)(?<!W)?AR(?!P)\\d*|Argentina'),
    'UY': re.compile('乌拉圭|烏拉圭|(\\s|-)?UY\\d*|Uruguay'),
    'PY': re.compile('巴拉圭|(\\s|-)?PY\\d*|Paraguay'),
    'JM': re.compile('牙买加|牙買加|(\\s|-)?JM(?!S)\\d*|Jamaica'),
    'SR': re.compile('苏里南|蘇里南|(\\s|-)?SR\\d*|Suriname'),
    'CW': re.compile('库拉索|庫拉索|(\\s|-)?CW\\d*|Curaçao'),
    'CO': re.compile('哥伦比亚|(\\s|-)?CO\\d*|Colombia'),
    'EC': re.compile('厄瓜多尔|(\\s|-)?EC\\d*|Ecuador'),
    'ES': re.compile('西班牙|\\b(\\s|-)?ES\\d*|Spain'),
    'PT': re.compile('葡萄牙|Portugal'),
    'IL': re.compile('以色列|(\\s|-)?IL\\d*|Israel'),
    'SA': re.compile('沙特|利雅得|吉达|Saudi|Saudi Arabia'),
    'MN': re.compile('蒙古|(\\s|-)?MN\\d*|Mongolia'),
    'AE': re.compile('阿联酋|迪拜|(\\s|-)?AE\\d*|Dubai|United Arab Emirates'),
    'AZ': re.compile('阿塞拜疆|(\\s|-)?AZ\\d*|Azerbaijan'),
    'AM': re.compile('亚美尼亚|亞美尼亞|(\\s|-)?AM\\d*|Armenia'),
    'KZ': re.compile('哈萨克斯坦|哈薩克斯坦|(\\s|-)?KZ\\d*|Kazakhstan'),
    'KG': re.compile('吉尔吉斯坦|吉尔吉斯斯坦|(\\s|-)?KG\\d*|Kyrghyzstan'),
    'UZ': re.compile('乌兹别克斯坦|烏茲別克斯坦|(\\s|-)?UZ\\d*|Uzbekistan'),
    'BR': re.compile('巴西|圣保罗|维涅杜|(?<!G)BR|Brazil'),
    'CL': re.compile('智利|(\\s|-)?CL\\d*|Chile|CHILE'),
    'PE': re.compile('秘鲁|祕魯|(\\s|-)?PE\\d*|Peru'),
    'CU': re.compile('古巴|Cuba'),
    'BT': re.compile('不丹|Bhutan'),
    'AD': re.compile('安道尔|(\\s|-)?AD\\d*|Andorra'),
    'MT': re.compile('马耳他|(\\s|-)?MT\\d*|Malta'),
    'MC': re.compile('摩纳哥|摩納哥|(\\s|-)?MC\\d*|Monaco'),
    'RO': re.compile('罗马尼亚|(\\s|-)?RO\\d*|Rumania'),
    'BG': re.compile('保加利亚|保加利亞|(\\s|-)?BG(?!P)\\d*|Bulgaria'),
    'HR': re.compile('克罗地亚|克羅地亞|(\\s|-)?HR\\d*|Croatia'),
    'MK': re.compile('北马其顿|北馬其頓|(\\s|-)?MK\\d*|North Macedonia'),
    'RS': re.compile('塞尔维亚|塞爾維亞|(\\s|-)?RS\\d*|Seville|Sevilla'),
    'CY': re.compile('塞浦路斯|(\\s|-)?CY\\d*|Cyprus'),
    'LV': re.compile('拉脱维亚|(\\s|-)?LV\\d*|Latvia|Latvija'),
    'MD': re.compile('摩尔多瓦|摩爾多瓦|(\\s|-)?MD\\d*|Moldova'),
    'SK': re.compile('斯洛伐克|(\\s|-)?SK\\d*|Slovakia'),
    'EE': re.compile('爱沙尼亚|(\\s|-)?EE\\d*|Estonia'),
    'BY': re.compile('白俄罗斯|白俄羅斯|(\\s|-)?BY\\d*|White Russia|Republic of Belarus|Belarus'),
    'BN': re.compile('文莱|汶萊|BRN|Negara Brunei Darussalam'),
    'GU': re.compile('关岛|關島|(\\s|-)?GU\\d*|Guam'),
    'FJ': re.compile('斐济|斐濟|(\\s|-)?FJ\\d*|Fiji'),
    'JO': re.compile('约旦|約旦|(\\s|-)?JO\\d*|Jordan'),
    'GE': re.compile('格鲁吉亚|格魯吉亞|(\\s|-)?GE(?!R)\\d*|Georgia'),
    'GI': re.compile('直布罗陀|直布羅陀|(\\s|-)(?<!CN2)?GI(?!A)\\d*|Gibraltar'),
    'SM': re.compile('圣马力诺|聖馬利諾|(\\s|-)?SM\\d*|San Marino'),
    'NP': re.compile('尼泊尔|(\\s|-)?NP\\d*|Nepal'),
    'FO': re.compile('法罗群岛|法羅群島|(\\s|-)?FO\\d*|Faroe Islands'),
    'AX': re.compile('奥兰群岛|奧蘭群島|(\\s|-)?AX\\d*|Åland'),
    'SI': re.compile('斯洛文尼亚|斯洛文尼亞|(\\s|-)?SI\\d*|Slovenia'),
    'AL': re.compile('阿尔巴尼亚|阿爾巴尼亞|(\\s|-)?AL\\d*|Albania'),
    'TL': re.compile('东帝汶|東帝汶|(\\s|-)?TL(?!S)\\d*|East Timor'),
    'PA': re.compile('巴拿马|巴拿馬|(\\s|-)?PA\\d*|Panama'),
    'BM': re.compile('百慕大|(\\s|-)?BM\\d*|Bermuda'),
    'GL': re.compile('格陵兰|格陵蘭|(\\s|-)?GL\\d*|Greenland'),
    'CR': re.compile('哥斯达黎加|(\\s|-)?CR\\d*|Costa Rica'),
    'VG': re.compile('英属维尔京|(\\s|-)?VG\\d*|British Virgin Islands'),
    'VI': re.compile('美属维尔京|(\\s|-)?VI\\d*|United States Virgin Islands'),
    'MX': re.compile('墨西哥|MX|MEX|MEX|MEXICO'),
    'ME': re.compile('黑山|(\\s|-)?ME\\d*|Montenegro'),
    'NL': re.compile('荷兰|荷蘭|尼德蘭|阿姆斯特丹|NL|Netherlands|Amsterdam'),
    'PL': re.compile('波兰|波蘭|(?<!I)(?<!IE)(\\s|-)?PL\\d*|POL|Poland'),
    'DZ': re.compile('阿尔及利亚|(\\s|-)?DZ\\d*|Algeria'),
    'BA': re.compile('波黑共和国|波黑|(\\s|-)?BA\\d*|Bosnia and Herzegovina'),
    'LI': re.compile('列支敦士登|(\\s|-)?LI\\d*|Liechtenstein'),
    'RE': re.compile('留尼汪|留尼旺|(\\s|-)?RE(?!LAY)\\d*|Réunion|Reunion'),
    'ZA': re.compile('南非|约翰内斯堡|(\\s|-)?ZA\\d*|South Africa|Johannesburg'),
    'EG': re.compile('埃及|(\\s|-)?EG\\d*|Egypt'),
    'GH': re.compile('加纳|(\\s|-)?GH\\d*|Ghana'),
    'ML': re.compile('马里|馬里|(\\s|-)?ML\\d*|Mali'),
    'MA': re.compile('摩洛哥|(\\s|-)?MA\\d*|Morocco'),
    'TN': re.compile('突尼斯|(\\s|-)?TN\\d*|Tunisia'),
    'LY': re.compile('利比亚|(\\s|-)?LY\\d*|Libya'),
    'KE': re.compile('肯尼亚|肯尼亞|(\\s|-)?KE\\d*|Kenya'),
    'RW': re.compile('卢旺达|盧旺達|(\\s|-)?RW\\d*|Rwanda'),
    'CV': re.compile('佛得角|維德角|(\\s|-)?CV\\d*|Cape Verde'),
    'AO': re.compile('安哥拉|(\\s|-)?AO\\d*|Angola'),
    'NG': re.compile('尼日利亚|尼日利亞|拉各斯|(\\s|-)?NG\\d*|Nigeria'),
    'MU': re.compile('毛里求斯|(\\s|-)?MU\\d*|Mauritius'),
    'OM': re.compile('阿曼|(\\s|-)?OM\\d*|Oman'),
    'BH': re.compile('巴林|(\\s|-)?BH\\d*|Bahrain'),
    'IQ': re.compile('伊拉克|(\\s|-)?IQ\\d*|Iraq'),
    'IR': re.compile('伊朗|(\\s|-)?IR\\d*|Iran'),
    'AF': re.compile('阿富汗|(\\s|-)?AF\\d*|Afghanistan'),
    'PK': re.compile('巴基斯坦|(\\s|-)?PK\\d*|Pakistan|PAKISTAN'),
    'QA': re.compile('卡塔尔|卡塔爾|(\\s|-)?QA\\d*|Qatar'),
    'SY': re.compile('叙利亚|敘利亞|(\\s|-)?SY\\d*|Syria'),
    'LK': re.compile('斯里兰卡|斯里蘭卡|(\\s|-)?LK\\d*|Sri Lanka'),
    'VE': re.compile('委内瑞拉|(\\s|-)?VE\\d*|Venezuela'),
    'GT': re.compile('危地马拉|(\\s|-)?GT\\d*|Guatemala'),
    'PR': re.compile('波多黎各|(\\s|-)?PR\\d*|Puerto Rico'),
    'KY': re.compile('开曼群岛|開曼群島|盖曼群岛|凯门群岛|(\\s|-)?KY\\d*|Cayman Islands'),
    'SJ': re.compile('斯瓦尔巴|扬马延|(\\s|-)?SJ\\d*|Svalbard|Mayen'),
    'HN': re.compile('洪都拉斯|Honduras'),
    'NI': re.compile('尼加拉瓜|(\\s|-)?NI\\d*|Nicaragua'),
    'AQ': re.compile('南极|南極|(\\s|-)?AQ\\d*|Antarctica'),
    'CN': re.compile('中国|中國|江苏|北京|上海|广州|深圳|杭州|徐州|青岛|宁波|镇江|沈阳|济南|回国|back|(\\s|-)?CN(?!2GIA)\\d*|China'),
}
