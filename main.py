from bs4 import BeautifulSoup
import flask
from flask import Flask, g, request
import json
import requests
from requests.auth import HTTPBasicAuth
import sqlite3
import sys

app = Flask(__name__)
app.config.from_object(__name__)

database = "data.db"

translations = {}

def retrieve_articles():
    url = "https://api.datamarket.azure.com/Bing/Search/v1/Composite"
    token = "uV5LSCwIXoqjVyZ2Y5C4S9nHpsGzuOS6u/0eKHtHcn4"
    response = requests.get(url,
        auth = HTTPBasicAuth(token, token),
        params = {
            "Sources": "'news'",
            "Query": "''",
            "Market": "'fr-FR'",
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
                "url": "http://www.lemonde.fr/proche-orient/article/2016/04/02/un-charnier-de-l-etat-islamique-decouvert-a-palmyre-en-syrie_4894601_3218.html",
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

        print 'insert into articles (url, title, description, image, text) values (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\')' % (article["url"], article["title"], article["description"], article["image"], article["text"])

        db = connect_db()
        db.execute("insert into articles (url, title, description, image, text) values (\"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (article["url"], article["title"], article["description"], article["image"], article["text"]))
        db.commit()

def translate_term(term):
    response = requests.get(
        url = "https://www.googleapis.com/language/translate/v2",
        params = {
            "key": "AIzaSyAqM11ClyXJss3ETYmhNFUWFWN5PkbSuo4",
            "q": term,
            "source": "fr",
            "target": "en",
        },
    )

    return json.loads(response.content)["data"]["translations"][0]["translatedText"]

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
    fetched_articles = []
    cur = g.db.execute('select * from articles order by id desc')
    entries = [dict(url=row[1], title=row[2], description=row[3], image=row[4], text=row[5]) for row in cur.fetchall()]
    articles = {"articles": entries}
    return flask.jsonify(**articles)

@app.route("/translate")
def translate():
    term = request.args.get("term")

    if term in translations:
        obj = {"translation": translations[term]}
        return flask.jsonify(**obj)
    else:
        translation = translate_term(term)
        obj = {"translation": translation}
        return flask.jsonify(**obj)

def connect_db():
    return sqlite3.connect(database)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        retrieve_articles()

    app.run(debug=True, host="0.0.0.0", port=80)
