import json
import newspaper
from newspaper import Article
import os
import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import time

def parse_article(url, lang, featured=0):
    article = Article(url, language=lang)
    article.download()
    article.parse()

    title = article.title
    image = article.top_image
    text = article.text
    authors = ",".join(article.authors)
    date = str(time.mktime(article.publish_date.timetuple()))

    db = connect_db()

    db.execute("insert into articles (url, title, image, text, authors, date, featured, language) values (?, ?, ?, ?, ?, ?, ?, ?)", (url, title, image, text, authors, date, featured, lang))
    db.commit()

    return {"url": url, "title": title, "image": image, "text": text, "authors": authors, "date": date, "language": lang}

def retrieve_articles(language):
    url = "https://api.datamarket.azure.com/Bing/Search/v1/Composite"
    token = "uV5LSCwIXoqjVyZ2Y5C4S9nHpsGzuOS6u/0eKHtHcn4"
    response = requests.get(url,
        auth = HTTPBasicAuth(token, token),
        params = {
            "Sources": "'news'",
            "Query": "''",
            "Market": "'%s'" % language,
            "$format": "json",
        },
        headers = {
            "Authorization": "Basic dVY1TFNDd0lYb3FqVnlaMlk1QzRTOW5IcHNHenVPUzZ1LzBlS0h0SGNuNDoqKioqKiBIaWRkZW4gY3JlZGVudGlhbHMgKioqKio=",
        }
    )

    lang = {"es-ES": "es", "fr-FR": "fr", "zh-CN": "zh-CN", "sv-SE": "sv"}[language]
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
      date text,
      featured integer not null,
      language text not null
    );""")

    db.execute("""create table if not exists translations (
      id integer primary key autoincrement,
      term text not null,
      translation text not null,
      language text not null
    );""")

    db.commit()

def connect_db():
    return sqlite3.connect("data.db")

init_db()

languages = ["es-ES", "fr-FR", "sv-SE"]

for language in languages:
    retrieve_articles(language)
