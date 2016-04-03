from bs4 import BeautifulSoup
import flask
from flask import Flask, request
import json
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

article_list = []
translations = {}

def retrieve_articles(retrieve_text):
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

        article = {
            "url": url,
            "image": image,
            "title": title,
            "description": description
        }

        if retrieve_text:
            diffbotResponse = requests.get(
                url = "http://api.diffbot.com/v3/article",
                params = {
                    "token": "0d5c56d2a7a3a5a4ad6c644b326993c2",
                    "url": "http://www.lemonde.fr/proche-orient/article/2016/04/02/un-charnier-de-l-etat-islamique-decouvert-a-palmyre-en-syrie_4894601_3218.html",
                },
            )

            articleText = json.loads(diffbotResponse.content)["objects"][0]["text"]
            article["text"] = articleText

        article_list.append(article)

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

@app.route("/articles")
def articles():
    articles = {"articles": articleList}
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

if __name__ == "__main__":
    # retrieve_articles(False)
    # translate_term("la lait")

    app.run(debug=True)
