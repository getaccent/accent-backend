import datetime
import json
import newspaper
from newspaper import Article
import os
import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import time

keys = json.load(file("keys.json", "r"))

def connect_db():
    return sqlite3.connect("data.db")

def parse_article(url, lang, featured=0, db=connect_db()):
    cur = db.execute("select * from articles where url=?", (url,))
    entries = [dict(id=row[0], url=row[1], title=row[2], image=row[3], text=row[4], authors=row[5], date=row[6], featured=row[7], language=row[8]) for row in cur.fetchall()]

    if len(entries) >= 1:
        return entries[0]

    article = Article(url)
    article.download()
    article.parse()

    title = article.title
    image = article.top_image
    text = article.text
    authors = ",".join(article.authors)
    date = int(time.mktime(article.publish_date.timetuple())) if type(article.publish_date) is datetime.datetime else 0

    db.execute("insert into articles (url, title, image, text, authors, date, featured, language) values (?, ?, ?, ?, ?, ?, ?, ?)", (url, title, image, text, authors, date, featured and len(text) >= 50, lang))
    db.commit()

    idquery = db.execute("select (id) from articles where url=?", (url,))
    id = [row[0] for row in idquery.fetchall()][0]

    return {"id": id, "url": url, "title": title, "image": image, "text": text, "authors": authors, "date": date, "language": lang}

def retrieve_articles(language):
    url = "https://api.datamarket.azure.com/Bing/Search/v1/Composite"
    token = keys["bing_search"]
    response = requests.get(url,
        auth = HTTPBasicAuth(token, token),
        params = {
            "Sources": "'news'",
            "Query": "''",
            "Market": "'%s'" % language,
            "$format": "json",
        },
        headers = {
            "Authorization": "Basic %s" % keys["bing_auth_header"],
        }
    )

    lang = {"en-US": "en", "es-ES": "es", "fr-FR": "fr", "de-DE": "de", "zh-CN": "zh-CN", "zh-TW": "zh-TW", "ja-JP": "ja", "it-IT": "it", "ko-KR": "ko", "sv-SE": "sv", "ru-RU": "ru"}[language]
    articles = json.loads(response.content)["d"]["results"][0]["News"]

    for art in articles:
        url = art["Url"]
        parse_article(url, lang, 1)

def init_db():
    if not os.path.isfile("data.db"):
        file("data.db", "w+")

    db = connect_db()

    db.execute("""create table if not exists articles (
      id integer primary key autoincrement,
      url text not null,
      title text not null,
      image text,
      text text not null,
      authors text,
      date integer not null,
      featured integer not null,
      language text
    );""")

    db.execute("""create table if not exists translations (
      id integer primary key autoincrement,
      term text not null,
      translation text not null,
      language text not null,
      target text not null
    );""")

    db.commit()

if __name__ == "__main__":
    init_db()

    languages = ["en-US", "es-ES", "fr-FR", "de-DE", "zh-CN", "zh-TW", "ja-JP", "it-IT", "ko-KR", "sv-SE", "ru-RU"]

    for language in languages:
        retrieve_articles(language)
