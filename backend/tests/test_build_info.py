"""The API has to say which commit it is running.

A stale image reported version 0.2.0 for four days while missing the endpoints
the cafe needed. The version string cannot catch that; the commit can.
"""

from app import version as version_module


def test_root_reports_the_commit(client):
    body = client.get("/").json()
    assert "commit" in body, "a one-line deploy check reads this field"
    assert "image" in body


def test_version_endpoint_reports_the_commit(client):
    body = client.get("/version").json()
    assert body["version"] == version_module.__version__
    assert "commit" in body


def test_commit_comes_from_the_build_stamp(monkeypatch):
    monkeypatch.setenv("GIT_SHA", "abc123def456")
    monkeypatch.setenv("FLY_IMAGE_REF", "registry.fly.io/lily-cafe-pos:deployment-01ABC")
    info = version_module.get_build_info()
    assert info["commit"] == "abc123def456"
    assert info["image"] == "lily-cafe-pos:deployment-01ABC"


def test_unstamped_build_says_so_rather_than_lying(monkeypatch):
    monkeypatch.delenv("GIT_SHA", raising=False)
    monkeypatch.delenv("FLY_IMAGE_REF", raising=False)
    info = version_module.get_build_info()
    assert info["commit"] == "unknown"
    assert info["image"] == "local"
