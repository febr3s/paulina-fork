import pytest
from flask import url_for

def test_author_search_valid(client):
    response = client.get(url_for('results'), query_string={
        'type_of_search': 'author',
        'query': 'test',
        'language': 'en'
    })
    assert response.status_code == 200
    assert b"Results" in response.data

def test_work_search_valid(client):
    response = client.get(url_for('results'), query_string={
        'type_of_search': 'work',
        'query': 'novel',
        'language': 'en'
    })
    assert response.status_code == 200
    assert b"Results" in response.data

def test_search_empty_query(client):
    response = client.get(url_for('results'), query_string={
        'type_of_search': 'author',
        'query': '',
        'language': 'en'
    })
    assert response.status_code == 200

def test_search_short_query(client):
    response = client.get(url_for('results'), query_string={
        'type_of_search': 'author',
        'query': 'a',
        'language': 'en'
    })
    assert response.status_code == 200