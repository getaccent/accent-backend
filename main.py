from flask import Flask, request
import flask
import json
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import urllib

app = Flask(__name__)

articleList = []

def send_request():
    try:
        url = "https://api.datamarket.azure.com/Bing/Search/v1/Composite"

        resp=requests.get(url, auth=HTTPBasicAuth('uV5LSCwIXoqjVyZ2Y5C4S9nHpsGzuOS6u/0eKHtHcn4', 'uV5LSCwIXoqjVyZ2Y5C4S9nHpsGzuOS6u/0eKHtHcn4'),
            params={
                "Sources": "'news'",
                "Query": "''",
                "Market": "'fr-FR'",
                "$format": "json",
            },
            headers={
                "Authorization": "Basic dVY1TFNDd0lYb3FqVnlaMlk1QzRTOW5IcHNHenVPUzZ1LzBlS0h0SGNuNDoqKioqKiBIaWRkZW4gY3JlZGVudGlhbHMgKioqKio=",
            },
        )

        myNews = json.loads(resp.content)["d"]["results"][0]["News"]

        for news_obj in myNews:
            url = news_obj["Url"]
            response = requests.get(url).content
            soup3 = BeautifulSoup(response, "html.parser")

            desc = soup3.findAll(attrs={"property":"og:image"})
            image = desc[0]['content'].encode('utf-8')

            desc2=soup3.findAll(attrs={"property":"og:title"})
            title=desc2[0]['content'].encode('utf-8')

            desc3=soup3.findAll(attrs={"property":"og:description"})
            description = ""
            if len(desc3) > 0:
                description=desc3[0]['content'].encode('utf-8')
            #og:title og:description

            try:
                response = requests.get(
                    url="http://api.diffbot.com/v3/article",
                    params={
                        "token": "0d5c56d2a7a3a5a4ad6c644b326993c2",
                        "url": "http://www.lemonde.fr/proche-orient/article/2016/04/02/un-charnier-de-l-etat-islamique-decouvert-a-palmyre-en-syrie_4894601_3218.html",
                    },
                )
                content=json.loads(response.content)["objects"][0]["text"]
                article = {"url": url, "image": image, "title":title, "description":description, "text": content}
                articleList.append(article)
                print article
            except requests.exceptions.RequestException:
                print('HTTP Request failed')
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

        #response obj 0 text

@app.route("/articles")
def articles():
    articles = {"articles": articleList}
    return flask.jsonify(**articles)

@app.route("/translate")
def translate():
    term = request.args.get("term")

def send_request2(term):
    try:
        response = requests.get(
            url="https://www.googleapis.com/language/translate/v2",
            params={
                "key": "AIzaSyAqM11ClyXJss3ETYmhNFUWFWN5PkbSuo4",
                "q": term,
                "source": "fr",
                "target": "en",
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

if __name__ == "__main__":
    send_request()
    #send_request3()
    # send_request2("la lait")
    app.run(debug=True)
