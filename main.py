from bs4 import BeautifulSoup
import flask
from flask import Flask, g, request
import json
import newspaper
from newspaper import Article
import os
import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import sys

app = Flask(__name__)
app.config.from_object(__name__)

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

def translate_term(term, language):
    response = requests.get(
        url = "https://www.googleapis.com/language/translate/v2",
        params = {
            "key": "AIzaSyAqM11ClyXJss3ETYmhNFUWFWN5PkbSuo4",
            "q": term,
            "source": language,
            "target": "en",
        },
    )

    translation = json.loads(response.content)["data"]["translations"][0]["translatedText"]
    g.db.execute("insert into translations (term, translation, language) values (\"%s\", \"%s\", \"%s\")" % (term, translation, language))
    g.db.commit()

    return translation

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route("/articles")
def articles():
    language = request.args.get("lang")
    fetched_articles = []
    cur = g.db.execute('select * from articles where language=\"%s\"' % language)
    entries = [(dict(url=row[1], title=row[2], text=row[3], image=row[4]) if len(row[4]) > 0 else dict(url=row[1], title=row[2], text=row[3])) for row in cur.fetchall()]
    articles = {"articles": entries}
    return flask.jsonify(**articles)

@app.route("/translate")
def translate():
    term = request.args.get("term")
    language = request.args.get("lang")

    cur = g.db.execute("select * from translations where term=\"%s\" and language=\"%s\"" % (term, language))
    entry = [dict(term=row[1], translation=row[2]) for row in cur.fetchall()]

    if len(entry) > 0:
        obj = {"translation": entry[0]["translation"]}
        return flask.jsonify(**obj)
    else:
        translation = translate_term(term, language)
        obj = {"translation": translation}
        return flask.jsonify(**obj)

def connect_db():
    return sqlite3.connect("data.db")

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

if __name__ == "__main__":
    init_db()

    if len(sys.argv) > 1:
        # languages = ["es-ES", "fr-FR", "zh-CN", "sv-SE"]
        languages = ["zh-CN"]
        for language in languages:
            retrieve_articles(language)

    app.run(debug=True, host="0.0.0.0", port=80)
