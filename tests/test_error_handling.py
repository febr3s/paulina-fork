import pytest
from flask import url_for

def test_404_error_page(client):
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert b"404 error" in response.data

def test_invalid_author_page(client):
    response = client.get(url_for('author_page', author_data='invalid_id'))
    assert response.status_code == 404

def test_invalid_work_page(client):
    response = client.get(url_for('work_page', work_data='invalid_id'))
    assert response.status_code == 404

def test_invalid_country_page(client):
    response = client.get(url_for('country_page', country_data='invalid_id'))
    assert response.status_code == 404

def test_error_handling_template(client):
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    assert b"404 error" in response.data
    assert b"Page not found" in response.data