from bs4 import BeautifulSoup
import flask
from flask import Flask, g, request
import json
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
    for article in articles:
        url = article["Url"]
        article_html = requests.get(url).content
        soup = BeautifulSoup(article_html, "html.parser")

        imageFind = soup.findAll(attrs={"property": "og:image"})
        image = imageFind[0]["content"].encode("utf-8")

        titleFind = soup.findAll(attrs={"property": "og:title"})
        title = titleFind[0]["content"].encode("utf-8")

        descriptionFind = soup.findAll(attrs={"property": "og:description"})
        description = ""

        if len(descriptionFind) > 0:
            description = descriptionFind[0]["content"].encode("utf-8")

        diffbotResponse = requests.get(
            url = "http://api.diffbot.com/v3/article",
            params = {
                "token": "0d5c56d2a7a3a5a4ad6c644b326993c2",
                "url": url,
            },
        )

        articleText = json.loads(diffbotResponse.content)["objects"][0]["text"]

        article = {
            "url": url,
            "image": unicode(image, 'utf-8'),
            "title": unicode(title, 'utf-8').replace("\"", "'"),
            "description": unicode(description, 'utf-8').replace("\"", "'"),
            "text": articleText.replace("\"", "'")
        }

        db = connect_db()
        db.execute("insert into articles (url, title, description, image, text, language) values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (article["url"], article["title"], article["description"], article["image"], article["text"], language))
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

    print response.content

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
    cur = g.db.execute('select * from articles order by id desc where language=\"%s\"' % language)
    entries = [dict(url=row[1], title=row[2], description=row[3], image=row[4], text=row[5]) for row in cur.fetchall()]
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
      description text,
      image text,
      text text,
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
        languages = ["es-ES", "fr-FR", "zh-CN", "sv-SE"]
        for language in languages:
            retrieve_articles(language)

    app.run(debug=True, host="0.0.0.0", port=80)
