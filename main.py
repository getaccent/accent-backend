import flask
from flask import Flask, g, request
from fetch import parse_article
import json
from newspaper import Article
import os
import requests
import sqlite3
import time

keys = json.load(open("keys.json", "r"))

app = Flask(__name__)
app.config.from_object(__name__)

def translate_term(term, language, target):
    response = requests.get(
        url = "https://www.googleapis.com/language/translate/v2",
        params = {
            "key": keys["google_translate"],
            "q": term,
            "source": language,
            "target": target,
        },
    )

    translation = response.json()["data"]["translations"][0]["translatedText"]
    g.db.execute("insert into translations (term, translation, language, target) values (\"%s\", \"%s\", \"%s\", \"%s\")" % (term, translation, language, target))
    g.db.commit()

    return translation

@app.before_request
def before_request():
    g.db = connect_db()
    g.sdb = connect_saved_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

    sdb = getattr(g, 'sdb', None)
    if sdb is not None:
        sdb.close()

@app.route("/articles")
def articles():
    language = request.args.get("lang")
    fetched_articles = []
    cur = g.db.execute('select * from articles where language=\"%s\" and featured=1 limit 30' % language)
    entries = [dict(id=row[0], url=row[1], title=row[2], image=row[3], text=row[4], authors=row[5], date=row[6], featured=row[7], language=row[8]) for row in cur.fetchall()]
    articles = {"articles": entries}
    return flask.jsonify(**articles)

@app.route("/parse")
def parse():
    url = request.args.get("url")

    a = Article(url)
    a.download()
    a.parse()

    text = a.text.replace("\"", "'")

    article = {
        "url": url,
        "image": a.top_image,
        "title": a.title.replace("\"", "'"),
        "text": text
    }

    return flask.jsonify(**article)

@app.route("/save", methods=['PUT'])
def save():
    num = request.args.get("num")
    url = request.args.get("url")

    g.sdb.execute("""create table if not exists n%s (
        id integer primary key autoincrement,
        url text not null
    )""" % num)

    g.sdb.execute("insert into n%s (url) values ('%s')" % (num, url))
    g.sdb.commit()

    return flask.jsonify(**{"success": True})

@app.route("/save", methods=['GET'])
def saved():
    num = request.args.get("num")

    cur = g.sdb.execute("select * from n%s" % num)
    urls = [row[1] for row in cur.fetchall()]

    articles = []

    for url in urls:
        article = parse_article(url, None, d=g.db)

        if article is not None:
            articles.append(article)

    result = {"articles": articles}
    return flask.jsonify(**result)

@app.route("/save", methods=['DELETE'])
def unsave():
    num = request.args.get("num")
    url = request.args.get("url")

    g.sdb.execute("delete from n%s where url=?" % num, (url,))
    g.sdb.commit()

    return flask.jsonify(**{"success": True})

@app.route("/translate")
def translate():
    term = request.args.get("term")
    language = request.args.get("lang")
    target = request.args.get("target")

    cur = g.db.execute("select * from translations where term=\"%s\" and language=\"%s\" and target=\"%s\"" % (term, language, target))
    entry = [dict(term=row[1], translation=row[2]) for row in cur.fetchall()]

    if len(entry) > 0:
        obj = {"translation": entry[0]["translation"]}
        return flask.jsonify(**obj)
    else:
        translation = translate_term(term, language, target)
        obj = {"translation": translation}
        return flask.jsonify(**obj)

def connect_db():
    return sqlite3.connect("data.db")

def connect_saved_db():
    return sqlite3.connect("saved.db")

if __name__ == "__main__":
    if not os.path.isfile("data.db"):
        open("data.db", "w+")

    if not os.path.isfile("saved.db"):
        open("saved.db", "w+")

    app.run(debug=True, host="0.0.0.0", port=80)
