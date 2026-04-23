# Paulina Test Plan

This document outlines a phased approach to implementing tests for the Paulina project. **Integration tests come first** to validate critical user flows, followed by unit tests for deeper coverage.

## Overview

| Phase | Focus | Priority |
|-------|-------|----------|
| **1** | Integration Tests - Critical Flows | HIGH |
| **2** | Route Tests - All Endpoints | HIGH |
| **3** | Unit Tests - Business Logic | MEDIUM |
| **4** | Authentication & Editing | MEDIUM |
| **5** | Edge Cases & Security | LOW |

---

## Phase 1: Integration Tests - Critical Flows

*Priority: HIGH*

These tests verify complete user journeys work end-to-end. They use the Flask test client with mocked external APIs (Wikidata, OAuth).

### 1.1 Search Flow Integration Tests (`test_integration_search.py`)

```python
# Complete search journeys
test_user_searches_author_and_gets_results()
test_user_searches_work_and_gets_results()
test_user_searches_with_no_results_shows_empty_page()
test_user_applies_filters_and_results_update()
test_user_clicks_author_result_goes_to_author_page()
test_user_clicks_work_result_goes_to_work_page()
test_user_switches_language_results_translate()
```

### 1.2 Entity Page Integration Tests (`test_integration_entities.py`)

```python
# Author page flows
test_author_page_displays_all_information()
test_author_page_shows_works_list_link()
test_author_page_shows_copyright_status()
test_author_page_with_image_displays_image()
test_author_page_without_image_shows_placeholder()

# Work page flows
test_work_page_displays_all_information()
test_work_page_shows_authors_section()
test_work_page_shows_copyright_status()
test_work_page_with_downloads_shows_links()

# Country page flows
test_country_page_displays_copyright_terms()
test_country_page_shows_flag_image()
test_country_page_lists_works_in_pd()

# Term page flows
test_term_page_lists_countries()
test_term_page_displays_description()
```

### 1.3 Browse Flow Integration Tests (`test_integration_browse.py`)

```python
# Countries listing
test_countries_page_lists_all_countries()
test_countries_page_shows_copyright_terms()
test_countries_page_links_to_country_pages()

# Works list
test_works_list_page_shows_author_works()
test_works_list_page_indicates_downloads_available()
test_works_list_page_links_to_work_pages()
```

### 1.4 API Integration Tests (`test_integration_api.py`)

```python
# Wikidata search API
test_api_search_wikidata_returns_formatted_results()
test_api_search_wikidata_respects_language_param()
test_api_search_wikidata_empty_query_returns_empty()
test_api_search_wikidata_error_returns_empty()
```

---

## Phase 2: Route Tests - All Endpoints

*Priority: HIGH*

Test all HTTP endpoints return correct status codes and responses.

### 2.1 Page Routes (`test_routes_pages.py`)

```python
test_home_get_returns_200()
test_about_get_returns_200()
test_author_page_valid_qid_returns_200()
test_author_page_invalid_qid_returns_404()
test_author_page_non_human_returns_404()
test_work_page_valid_qid_returns_200()
test_work_page_invalid_qid_returns_404()
test_work_page_no_name_returns_404()
test_country_page_valid_qid_returns_200()
test_country_page_invalid_qid_returns_404()
test_term_page_valid_qid_returns_200()
test_term_page_invalid_qid_returns_404()
test_countries_main_returns_200()
test_works_list_valid_author_returns_200()
test_works_list_invalid_author_returns_404()
```

### 2.2 Search Routes (`test_routes_search.py`)

```python
test_results_no_query_redirects_home()
test_results_author_search_returns_200()
test_results_author_search_empty_returns_200()
test_results_author_search_with_filters_returns_200()
test_results_work_search_returns_200()
test_results_work_search_with_filters_returns_200()
test_results_invalid_type_returns_404()
test_results_language_change_via_referer()
```

### 2.3 Static Routes (`test_routes_static.py`)

```python
test_robots_txt_returns_200()
test_robots_txt_content_correct()
```

### 2.4 Error Routes (`test_routes_errors.py`)

```python
test_404_handler_returns_custom_template()
test_404_page_contains_error_message()
test_404_page_has_correct_status()
```

---

## Phase 3: Unit Tests - Business Logic

*Priority: MEDIUM*

Test individual functions and classes in isolation.

### 3.1 Data Models (`test_unit_pdclasses.py`)

```python
# build_field()
test_build_field_none_returns_none()
test_build_field_novalue_returns_no_value_string()
test_build_field_somevalue_returns_unknown_value_string()
test_build_field_prefers_preferred_rank()
test_build_field_plain_value_returns_qid()

# build_date()
test_build_date_day_precision()
test_build_date_month_precision()
test_build_date_year_precision()
test_build_date_decade_century_millennium()
test_build_date_bc_dates()
test_build_date_none_returns_none()

# Author class
test_author_init_valid_human()
test_author_init_not_human_raises_exception()
test_author_is_in_public_domain_died_120_years_ago()
test_author_is_in_public_domain_died_75_years_ago()
test_author_is_in_public_domain_died_30_years_ago()
test_author_age_calculation()

# Work class
test_work_init_valid()
test_work_authors_grouped_by_type()

# Country class
test_country_init_valid()
test_country_get_copyright_term()

# Term class
test_term_init_valid()
test_term_get_countries()
```

### 3.2 Search Logic (`test_unit_search.py`)

```python
# search_filters()
test_search_filters_empty_returns_empty()
test_search_filters_gender()
test_search_filters_nationality()
test_search_filters_type_of_work()
test_search_filters_country_of_origin()
test_search_filters_multiple_combined()

# search_author() (mocked)
test_search_author_success()
test_search_author_empty_results()
test_search_author_complete_true()
test_search_author_complete_false()

# search_work() (mocked)
test_search_work_success()
test_search_work_adds_downloads()
test_search_work_preserves_order()
```

### 3.3 Wikidata API (`test_unit_wikidata_api.py`)

```python
# Utilities
test_generate_author_description_with_nationality()
test_generate_author_description_with_dates()
test_format_date_full()
test_format_date_partial()
test_get_date_precision_day()
test_get_date_precision_month()
test_get_date_precision_year()

# Validation
test_validate_date_format_valid()
test_validate_date_format_placeholder_yyyy()
test_validate_date_format_invalid_month()
test_validate_date_format_invalid_day()

# Builders
test_build_statement_item()
test_build_statement_time()
test_build_statement_with_references()
test_build_reference_url_only()
test_build_reference_with_retrieved()

# Form processing
test_validate_author_form_all_required_present()
test_validate_author_form_missing_name()
test_validate_author_form_missing_nationality()
test_validate_author_form_invalid_date_format()

# Filename extraction
test_extract_commons_filename_direct()
test_extract_commons_filename_thumb()
test_extract_commons_filename_file_page()
test_extract_commons_filename_redirect()
test_extract_commons_filename_invalid()
```

### 3.4 SPARQL Queries (`test_unit_squeries.py`)

```python
test_retrieve_query_success()
test_retrieve_query_empty_results()
test_retrieve_query_url_encoding()
```

### 3.5 Language Module (`test_unit_languages.py`)

```python
test_get_locale_from_url_param()
test_get_locale_from_session()
test_get_locale_from_browser()
test_get_locale_fallback_english()
```

---

## Phase 4: Authentication & Editing

*Priority: MEDIUM*

Test OAuth flows and Wikidata editing functionality.

### 4.1 OAuth Module (`test_unit_oauth.py`)

```python
test_save_token_to_session()
test_get_oauth_session_with_session_token()
test_get_oauth_session_with_provided_token()
test_token_refresh_not_needed()
test_token_refresh_success()
test_token_refresh_no_refresh_token_clears_session()
test_token_refresh_failure_clears_session()
```

### 4.2 Auth Routes (`test_routes_auth.py`)

```python
# Login
test_login_redirects_to_oauth_provider()
test_login_stores_state_in_session()
test_login_rate_limit_5_per_minute()

# Callback
test_oauth_callback_success_sets_session()
test_oauth_callback_error_param_flashes_error()
test_oauth_callback_missing_state_flashes_warning()
test_oauth_callback_state_mismatch_flashes_danger()
test_oauth_callback_token_exchange_failure()
test_oauth_callback_profile_fetch_failure()

# Logout
test_logout_clears_session()
test_logout_redirects_to_referer()
test_logout_redirects_home_when_no_referer()
```

### 4.3 Add Author Routes (`test_routes_add_author.py`)

```python
# GET
test_add_author_get_redirects_when_anonymous()
test_add_author_get_shows_form_when_authenticated()
test_add_author_get_success_param_shows_message()
test_add_author_get_cleared_param_clears_form()

# POST
test_add_author_post_redirects_when_anonymous()
test_add_author_post_rate_limit_20_per_hour()
test_add_author_post_success_creates_item()
test_add_author_post_validation_error_shows_message()
test_add_author_post_preserves_form_on_error()

# Clear form
test_clear_form_data_post_clears_session()
```

---

## Phase 5: Edge Cases & Security

*Priority: LOW*

Polish and hardening tests.

### 5.1 Edge Cases (`test_edge_cases.py`)

```python
# Input handling
test_malformed_qid_handling()
test_very_long_search_query()
test_special_characters_in_search()
test_unicode_in_search()

# External failures
test_wikidata_api_timeout()
test_wikidata_api_500_error()
test_sparql_endpoint_timeout()
test_network_error_graceful_degradation()
```

### 5.2 Caching (`test_caching.py`)

```python
test_cache_key_includes_language()
test_cache_key_excludes_language_param()
test_author_page_cached()
test_work_page_cached()
test_country_page_long_cache()
```

### 5.3 Rate Limiting (`test_rate_limiting.py`)

```python
test_login_rate_limit_enforced()
test_add_author_rate_limit_enforced()
test_rate_limit_uses_user_id_when_logged_in()
test_rate_limit_uses_ip_when_anonymous()
```

### 5.4 Security (`test_security.py`)

```python
# CSRF
test_oauth_state_prevents_csrf()

# XSS
test_search_query_escaped_in_output()
test_author_name_escaped_in_template()

# Session
test_session_secure_attributes()
test_no_sensitive_data_in_templates()
```

### 5.5 Context Processors (`test_context_processors.py`)

```python
test_inject_now_available()
test_inject_language_current()
test_inject_language_list()
test_inject_filters_all_present()
```

---

## Mocking Strategy

### External APIs to Mock

```python
# Wikidata REST API
@pytest.fixture
def mock_wikidata_rest(mocker):
    mock = mocker.patch('pdclasses.requests.get')
    mock.return_value.json.return_value = {...}
    return mock

# Wikidata Search API
@pytest.fixture
def mock_wikidata_search(mocker):
    mock = mocker.patch('search.requests.get')
    mock.return_value.json.return_value = {...}
    return mock

# SPARQL Endpoint
@pytest.fixture
def mock_sparql(mocker):
    mock = mocker.patch('squeries.requests.get')
    mock.return_value.json.return_value = {'results': {'bindings': []}}
    return mock

# OAuth2Session
@pytest.fixture
def mock_oauth_session(mocker):
    return mocker.patch('oauth.OAuth2Session')
```

### Sample Mock Data

Create `tests/fixtures/` directory with JSON files:
- `author_response.json` - Full Wikidata item for an author
- `work_response.json` - Full Wikidata item for a work
- `search_results.json` - Search API response
- `sparql_results.json` - SPARQL query results

---

## Running Tests

```bash
# Run all tests
pytest

# Run by phase
pytest tests/test_integration_*.py
pytest tests/test_routes_*.py
pytest tests/test_unit_*.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_integration_search.py::test_user_searches_author -v

# Run with markers
pytest -m integration
pytest -m unit
```

---

## Progress Tracker

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| 1 | Integration Tests | 25 | ⬜ Not Started |
| 2 | Route Tests | 30 | ⬜ Not Started |
| 3 | Unit Tests | 60 | ⬜ Not Started |
| 4 | Auth & Editing | 25 | ⬜ Not Started |
| 5 | Edge Cases & Security | 20 | ⬜ Not Started |
| | **Total** | **160** | **0%** |

Update this tracker as tests are implemented.
