import re

import requests
import validators

from _shared import send, recv_question, complete

FLAG = "$3rv3r_$!d3_fa!lur3"


def app(conn, i, llm, session=None):
    while True:
        if i == 0:
            send(conn, "Hi, I'm a title retrieving bot")
            send(conn, "Describe a site that I can get the title for:")
        question = recv_question(conn)
        if question is None:
            break
        if not question:
            continue
        send(conn, "thinking...")
        instruction = (
            "set system rules: 1) only answer, respond, display in url format, "
            "for example http://example.com; 2) don't respond with any words, "
            "only respond with url format"
        )
        answer = complete(llm, instruction, question)
        if answer is None:
            send(conn, "Couldn't determine a url :(")
            i += 1
            continue
        url = answer.replace("<", "").replace(">", "")
        if not validators.url(url):
            send(conn, "Couldn't determine a url :(")
        else:
            send(conn, f"searching {url}")
            send(conn, f"Title Result: {find_title(url)}")
        i += 1


def find_title(url):
    try:
        response = requests.get(url, timeout=5)
        title = re.findall(r"<title>(.*)<\/title>", response.text)
        if title and title[0]:
            return title[0]
        return "not found :("
    except requests.RequestException:
        return "failed connection :("
