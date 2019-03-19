# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as bs
import re
import os
import random
from time import sleep

RESULT_PATH = './RESULT'
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'cookie':'''Your cookie'''
    }
pa_num = re.compile(r'(\d+).*')  # 匹配数字模式


def request_url(url, headers, retry_time=5, timeout=10):
    sleep(random.randint(1, 5))
    while retry_time > 0:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            res_ctx = response.text  # .content
        except Exception as e:
            print("访问{}时出现异常:{}剩余重试次数{}".format(url, e, str(retry_time)))
            retry_time -= 1
        else:
            return res_ctx
    else:
        print("重试次数耗尽，访问{}失败".format(url))
        return None


def get_50_hot():
    res_html = request_url('https://www.zhihu.com/hot', headers)
    soup = bs(res_html, "html.parser")
    # <div class="HotItem-content"><a href="https://www.zhihu.com/question/26440561" title="有哪些值得每天一看的网站？">...
    item_list = soup.find_all('div', attrs={'class':'HotItem-content'})
    res_list = []
    for item in item_list:
        href = item.find('a').get('href')
        title = item.find('a').get('title')
        # print(title, href)
        res_list.append([href, title])
    return res_list


def get_answer_list(question_id, answer_num):
    res_list = []
    offset = 0
    # 正则匹配前10条评论的answer ID
    ids_pattern = re.compile(r"\"id\":(\d+),\"type\":\"answer\"")
    while offset < answer_num:
        # 知乎官方提供的对问题查询评论的API，如果直接访问问题，默认只会返回两条评论。
        answer_search_api = "https://www.zhihu.com/api/v4/questions/{}/answers?limit=10&offset={}".format(question_id, offset)
        # limit: 请求answer数
        # offset: answer偏移量
        res_ctx = request_url(answer_search_api, headers)
        answer_id_list = ids_pattern.findall(res_ctx) if res_ctx else None
        offset = offset + 10
        if not answer_id_list == None:
            res_list.append(answer_id_list)
    return res_list


def get_answer(question_id, answer_id):
    answer_url = "https://www.zhihu.com/question/{}/answer/{}".format(question_id, answer_id)
    res_ctx = request_url(answer_url, headers)
    # 使用BeautifulSoup4解析爬取的html文件
    soup = bs(res_ctx, "html.parser")
    # 对特定目标使用属性进行筛选
    qa_content = soup.find(name="div", attrs={"class": "QuestionAnswer-content"})
    author_id = qa_content.find(name="meta", attrs={"itemprop": "name"})["content"]
    print("------正在爬取用户 {} 的评论".format(author_id))
    author_space = qa_content.find(name="meta", attrs={"itemprop": "url"})["content"]
    upvote_count = qa_content.find(name="meta", attrs={"itemprop": "upvoteCount"})["content"]
    cmt_content = qa_content.find(name="div", attrs={"class": "RichContent-inner"}).text
    return author_id, author_space, upvote_count, cmt_content


def get_question_tag():
    return None


def validateTitle(title):
    # 去除标题中的非法字符
    rstr = r'[\/\\\:\*\?\"\<\>\|]'
    new_title = re.sub(rstr, '', title)
    return new_title


def save_question(url, title, index):
    question_id = url.split("/")[-1]
    soup = bs(request_url(url, headers), "html.parser")
    answer_num = int(pa_num.findall(soup.h4.text)[0])  # 获取回答数
    question_tag = get_question_tag()  # 获取话题标签
    answer_list = get_answer_list(question_id, answer_num)  # 获取评论id列表
    title = validateTitle(title)
    filename = title if len(title) <= 20 else title[:20]
    filename = 'Top{}-{}.txt'.format(str(index + 1), filename)
    with open(RESULT_PATH + '/' + filename, 'w', encoding='utf-8') as f:
        f.write(title + '\t' + answer_num + '回答\n\n')  # 第1行
        # 写入回答
        for answer_id in answer_list:
            try:
                author_id, author_space, upvote_count, cmt_content = get_answer(question_id, answer_id)
                f.write(str(author_id) + "\t" + author_space + "\t点赞数：" + str(upvote_count) + "\n")
                f.write(str(cmt_content) + "\n")
            except Exception as e:
                print("评论{}写入时异常:{}".format(answer_id, e))
        f.close()
    return question_tag


def save_zhuanlan(url, title, index):
    # 专栏内容暂时不获取
    return None


if __name__ == '__main__':
    if not os.path.exists(RESULT_PATH):
        # 初始化
        os.mkdir(RESULT_PATH)

    top_list = get_50_hot()
    # print(top_list)
    
    for index, item in enumerate(top_list):
        # 逐条访问前50热点
        url = item[0]
        if 'question' in url:
            tag = save_question(url, item[1], index)
        elif 'zhuanlan' in url:
            tag = save_zhuanlan(url, item[1], index)
            

