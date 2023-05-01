import json
import random
from time import sleep
import requests
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['news']
collection = db['source_html']


def get_settings_ids(coll, query=None):
    if not query:
        query = {}

    return [x['ID'] for x in coll.find(query)] or []


def get_source_document(source_id):
    return collection.find_one({'ID': source_id})


def pretty_print(obj):
    print(json.dumps(obj, indent=4))


if __name__ == '__main__':
    url = 'http://localhost:5000/content'
    with_content = False

    if not with_content:
        settings_ids = get_settings_ids(db['source_settings'], {'url': {'$regex': 'rss_feed|news_feed|feed'}})
    else:
        settings_ids = ['11111', '11112']

    for sid in settings_ids:
        data = dict()

        document = get_source_document(source_id=sid)
        if not document:
            document = {'type': 'list', 'html': ''}

        data['s_id'] = sid
        data['type'] = document['type']
        data['content'] = document['html']
        headers = {'Content-type': 'application/json'}

        response = requests.post(url, data=json.dumps(data), headers=headers)
        print(response.text)

        sleep(2)
