import json
import re

import flask
import requests

UBEREATS_HOST = 'https://www.ubereats.com'
SEARCH_COORDINATES = (47.6276544, -122.341216)

app = flask.Flask(__name__)

def get_stores():
    session = requests.Session()
    resp = session.get(UBEREATS_HOST + '/stores/')
    config = json.loads(re.search(r'window\.CONFIG = (.+?);', resp.text).group(1))
    endpoint = config['rtapi']['clientBaseUrl'] + config['rtapi']['endpoints']['postEatsBootstrapEater']
    resp = session.post(UBEREATS_HOST + endpoint,
        headers={
            'x-csrf-token': config['csrf']['token'],
        },
        json={
            'targetLocation': {
                'latitude': SEARCH_COORDINATES[0],
                'longitude': SEARCH_COORDINATES[1],
            },
        })
    return process_raw_stores(resp.json()['marketplace']['stores'])

def process_raw_stores(stores):
    for store in stores:
        yield {
            'uuid': store['uuid'],
            'image': store.get('largeHeroImageUrl', store.get('heroImageUrl', '')),
            'orderable': store['isOrderable'],
            'name': store['title'],
            'eta': tuple(store['etdInfo']['dropoffETARange'][p] for p in ('min', 'max')),
            'tags': sorted([t['name'] for t in store.get('tags', [])]),
            'price': store.get('priceBucket', None),
        }

def get_sorted_stores():
    return sorted(sorted(get_stores(), key=lambda k: k['name']), key=lambda k: not k['orderable'])

@app.route('/')
def index():
    return flask.render_template('index.html', stores=get_sorted_stores())
