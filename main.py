import flask
from flask import Flask, g, request
import json
from newspaper import Article
import os
import requests
import sqlite3


app = Flask(__name__)
app.config.from_object(__name__)

def translate_term(term, language):
    response = requests.get(
        url = "https://www.googleapis.com/language/translate/v2",
        params = {
            "key": "AIzaSyARW9JcFJBS92x2IR-6dSYAI_l0R55xCrA",
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
    cur = g.db.execute('select * from articles where language=\"%s\"' % (language)
    entries = [(dict(url=row[1], title=row[2], text=row[3], image=row[4]) if len(row[4]) > 0 else dict(url=row[1], title=row[2], text=row[3])) for row in cur.fetchall()]
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
    
@app.route("/save", methods=['POST'])
def save():
    num = request.args.get("num")
    url = request.args.get("url")

    a = Article(url)
    a.download()
    a.parse()

    text = a.text.replace("\"", "'")

    g.sdb.execute("""create table if not exists n%s (
        id integer primary key autoincrement,
        url text not null,
        status integer not null
    )""" % num)

    g.sdb.execute("insert into n%s (url, status) values ('%s', 0)" % (num, url))
    g.sdb.commit()

    return flask.jsonify(**{"success": True})

@app.route("/saved")
def saved():
    num = request.args.get("num")
    url = request.args.get("url")
    a = Article(url)
    a.download()
    a.parse()

    cur = g.sdb.execute("select * from n%s" % num)
    entries = [dict(url=row[1], status=row[2],title=row[3], text=row[3],image=row[5],num=row[6]) for row in cur.fetchall()]
    result = {
        "entries": entries;
        "url":url
        "image":a.top_image,
        "title":a.title.replace("\"","''),
        "text":text
        }

    return flask.jsonify(**result)

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

def connect_saved_db():
    return sqlite3.connect("saved.db")

if __name__ == "__main__":
    if not os.path.isfile("data.db"):
        file("data.db", "w+")

    if not os.path.isfile("saved.db"):
        file("saved.db", "w+")

    app.run(debug=True, host="0.0.0.0", port=80)
