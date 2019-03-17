# -*- coding: utf-8 -*-
import bs4
import re
import os
import shutil
import requests
from bs4 import BeautifulSoup

# 爬虫结果保存路径
RESULT_PATH = "./RESULT"
if os.path.exists(RESULT_PATH):
    # 初始化
    shutil.rmtree(RESULT_PATH)
    os.mkdir(RESULT_PATH)


def request_url(url, headers, retry_time=5, timeout=10):
    while retry_time > 0:
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            res_ctx = response.text
        except Exception as e:
            print("访问{}时出现异常:{}剩余重试次数{}".format(url, e, str(retry_time)))
            retry_time -= 1
        else:
            return res_ctx
    else:
        print("重试次数耗尽，访问{}失败".format(url))
        return None


# headers包含两个字段
# user-agent表示模拟浏览器信息
# cookie中保存了用户的登录信息
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'cookie':'''Your cookie'''
    }

url = "https://www.zhihu.com/hot"
res_ctx = request_url(url, headers)  # 请求热点页面 -> 获取热点页面的html
if not res_ctx:
    exit()

# 使用正则匹配50条热点的索引+链接+标题
hot_pattern = re.compile(r"<div class=\"HotItem-index\">.*?(\d+).*?><a href=\"(.*?)\" title=\"(.*?)\"")
# 50条（索引，链接，标题）的列表
hot_50_list = hot_pattern.findall(res_ctx)
# print(hot_50_list)

for index, one in enumerate(hot_50_list):
    # 逐条访问50条热点的前10条评论
    url = one[1]  # 热点信息的链接
    with open(RESULT_PATH + "/" + "Top{}.txt".format(str(index + 1)), "w", encoding="utf-8")as f:
        print("正在爬取：{} 的前10条评论".format(one[0] + " " + one[2]))
        if "question" in url:
            # question类文章
            f.write(one[2] + "\n\n")
            question_id = url.split("/")[-1]
            # 知乎官方提供的对问题查询评论的API，如果直接访问问题，默认只会返回两条评论。
            top_10_answer_search_api = "https://www.zhihu.com/api/v4/questions/{}/answers?limit=10&offset={}".format(question_id,offset)
            # limit: 请求answer数
            # offset: answer偏移量
            res_ctx = request_url(top_10_answer_search_api, headers)
            # 正则匹配前10条评论的answer ID
            ids_pattern = re.compile(r"\"id\":(\d+),\"type\":\"answer\"")
            answer_id_list = ids_pattern.findall(res_ctx) if res_ctx else None
            for answer_id in answer_id_list:
                answer_url = "https://www.zhihu.com/question/{}/answer/{}".format(question_id, answer_id)
                res_ctx = request_url(answer_url, headers)
                # 使用BeautifulSoup4解析爬取的html文件
                soup = bs4.BeautifulSoup(res_ctx, "html.parser")
                # 对特定目标使用属性进行筛选
                qa_content = soup.find(name="div", attrs={"class": "QuestionAnswer-content"})
                author_id = qa_content.find(name="meta", attrs={"itemprop": "name"})["content"]
                print("------正在爬取用户 {} 对问题 {} 的评论".format(author_id, one[2]))
                author_space = qa_content.find(name="meta", attrs={"itemprop": "url"})["content"]
                upvote_count = qa_content.find(name="meta", attrs={"itemprop": "upvoteCount"})["content"]
                f.write(str(author_id) + "\t" + author_space + "\t点赞数：" + str(upvote_count) + "\n")
                cmt_content = qa_content.find(name="div", attrs={"class": "RichContent-inner"}).text
                f.write(str(cmt_content) + "\n")
        elif "zhuanlan" in url:
            p_id = url.split("/")[-1]
            top_10_comment_search_api = "https://www.zhihu.com/api/v4/articles/{}/root_comments?include=data%5B*%5D.author%2Ccontent%2Cvote_count%2Corder=normal&limit=10&offset=0&status=open".format(p_id)
            res_ctx = request_url(top_10_comment_search_api, headers)
            # 将json字符串转化为python数据结构可以接受的字段
            datas = eval(res_ctx.replace("false", "False").replace("true", "True").replace("null", "None"))["data"]
            for data in datas:
                author_info = str(data["author"])
                author_id = re.search(r"\'name\': \'(.*?)\'", author_info).group(1)
                # 获取目标信息
                print("------正在爬取用户 {} 对问题 {} 的评论".format(author_id, one[2]))
                author_space_url = "https://www.zhihu.com/people/"
                author_space = author_space_url + re.search(r"\'url_token\': \'(.*?)\'", author_info).group(1)
                upvote_count = data["vote_count"]
                f.write(str(author_id) + "\t" + author_space + "\t点赞数：" + str(upvote_count) + "\n")
                cmt_content = re.sub(r"</?.*?>", "", data["content"])
                f.write(str(cmt_content) + "\n")
