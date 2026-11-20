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
    ("/", "Role Login Hub"),
    ("/login", "Role Login Hub"),
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
    if route not in ["/", "/login", "/portal/gateway"]:
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


def test_login_hub_accessible(client):
    """Verifies that the /login endpoint loads successfully with role tabs."""
    res = client.get("/login")
    assert res.status_code == 200
    assert "Hospital Clinical RAG" in res.text
    assert "Role Login Hub" in res.text
    assert "Chief Medical Officer" in res.text
    assert "Treating Doctor" in res.text
    assert 'src="/login.js"' in res.text


def test_portal_common_script_has_route_guard_and_logout(client):
    """Verifies that portal_common.js contains fail-closed route redirection and logout handling."""
    res = client.get("/portal_common.js")
    assert res.status_code == 200
    assert "auth_required" in res.text
    assert "logoutBtn" in res.text
    assert "sessionStorage.removeItem" in res.text


def test_api_login_http_validation(client):
    """Verifies HTTP /api/auth/login enforces password validation and fail-closed security."""
    # 1. Valid credentials
    res_ok = client.post("/api/auth/login", json={"user_id": "DR_302", "password": "doc@123"})
    assert res_ok.status_code == 200
    assert "token" in res_ok.json()
    assert res_ok.json()["persona"]["role"] == "Treating Doctor"

    # 2. Invalid password -> 401
    res_bad_pwd = client.post("/api/auth/login", json={"user_id": "DR_302", "password": "wrong_password"})
    assert res_bad_pwd.status_code == 401
    assert "FAIL-CLOSED" in res_bad_pwd.json()["detail"]

    # 3. Missing password -> 401 or 422
    res_no_pwd = client.post("/api/auth/login", json={"user_id": "DR_302"})
    assert res_no_pwd.status_code in [401, 422]

    # 4. Unknown user -> 401
    res_unk = client.post("/api/auth/login", json={"user_id": "FAKE_USER", "password": "any"})
    assert res_unk.status_code == 401
    assert "FAIL-CLOSED" in res_unk.json()["detail"]



