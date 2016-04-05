import json
import newspaper
from newspaper import Article
import os
import requests
from requests.auth import HTTPBasicAuth
import sqlite3

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

    articles = json.loads(response.content)["d"]["results"][0]["News"]

    for art in articles:
        url = art["Url"]

        a = Article(url, lang=language.split("-")[0])
        a.download()
        a.parse()

        text = a.text.replace("\"", "'")

        if len(text) < 10:
            continue

        article = {
            "url": url,
            "image": a.top_image,
            "title": a.title.replace("\"", "'"),
            "text": text
        }

        db = connect_db()
        db.execute("insert into articles (url, title, image, text, language) values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (article["url"], article["title"], article["image"], article["text"], language))
        db.commit()

def init_db():
    if not os.path.isfile("data.db"):
        file("data.db", "w+")

    db = connect_db()

    db.execute("""create table if not exists articles (
      id integer primary key autoincrement,
      url text not null,
      title text not null,
      text text not null,
      image text,
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

languages = ["es-ES", "fr-FR", "zh-CN", "sv-SE"]

for language in languages:
    retrieve_articles(language)
