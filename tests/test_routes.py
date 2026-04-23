import pytest
from flask import url_for

def test_home_page(client):
    response = client.get(url_for('home'))
    assert response.status_code == 200
    assert b"Home" in response.data

def test_about_page(client):
    response = client.get(url_for('about'))
    assert response.status_code == 200
    assert b"About" in response.data

def test_results_page_no_query(client):
    response = client.get(url_for('results'))
    assert response.status_code == 302  # Should redirect to home

def test_author_page_not_found(client):
    response = client.get(url_for('author_page', author_data='invalid'))
    assert response.status_code == 404

def test_404_error_handler(client):
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b"404 error" in response.data