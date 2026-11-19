"""
Tests for Role-Specific Portal Pages and Route Accessibility.
Verifies all 7 portals load properly and return HTTP 200.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


PORTAL_ROUTES = [
    ("/", "Role Gateway & Portals Directory"),
    ("/portal/gateway", "Role Gateway & Portals Directory"),
    ("/portal/cmo", "Chief Medical Officer Portal"),
    ("/portal/dept-head", "Department Head Portal"),
    ("/portal/doctor", "Treating Doctor Clinical Station"),
    ("/portal/nurse", "Nurse Ward Station"),
    ("/portal/billing", "Front Desk & Billing Desk"),
    ("/portal/admin", "System Admin Security Console")
]


@pytest.mark.parametrize("route,title_keyword", PORTAL_ROUTES)
def test_portal_routes_accessible(client, route, title_keyword):
    """Verifies that all role portal endpoints return HTTP 200 and serve their dedicated HTML."""
    res = client.get(route)
    assert res.status_code == 200
    assert title_keyword in res.text
    assert "Hospital RAG" in res.text
    assert 'href="/style.css"' in res.text
    if route != "/" and route != "/portal/gateway":
        assert 'src="/portal_common.js"' in res.text


def test_static_assets_and_fallbacks(client):
    """Verifies root static assets and fallback subpath routes all return HTTP 200."""
    # Root paths
    css_res = client.get("/style.css")
    assert css_res.status_code == 200
    assert "text/css" in css_res.headers.get("content-type", "")

    js_res = client.get("/portal_common.js")
    assert js_res.status_code == 200

    fav_res = client.get("/favicon.ico")
    assert fav_res.status_code == 200
    assert "image/svg+xml" in fav_res.headers.get("content-type", "")

    # Subpath /portal/ fallbacks to prevent 404 when relative links are requested
    portal_css_res = client.get("/portal/style.css")
    assert portal_css_res.status_code == 200
    assert "text/css" in portal_css_res.headers.get("content-type", "")

    portal_js_res = client.get("/portal/portal_common.js")
    assert portal_js_res.status_code == 200
