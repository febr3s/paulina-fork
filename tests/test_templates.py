from flask import url_for

def test_base_template(client):
    """Test that base elements are present in all pages"""
    response = client.get(url_for('home'))
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'<html lang="' in response.data
    assert b'<head>' in response.data
    assert b'<footer>' in response.data

def test_template_variables(client):
    """Test that templates receive expected variables"""
    home_response = client.get(url_for('home'))
    about_response = client.get(url_for('about'))
    
    # Check title tag exists in response
    assert b'<title>' in home_response.data
    assert b'<title>' in about_response.data
    
    # Check page-specific content
    assert b'Home' in home_response.data
    assert b'About' in about_response.data