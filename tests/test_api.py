def test_current_edition(client):
    res = client.get("/editions/current")
    assert res.status_code == 200
    body = res.json()
    assert body["issue_number"] >= 1
    assert body["stories"]
    assert "sources_scanned" in body["week_in_numbers"]


def test_story_and_search(client):
    story = client.get("/stories/ladybird-independent-browser-engine")
    assert story.status_code == 200
    data = story.json()
    assert data["is_demo"] is False
    assert data["projects"]
    search = client.get("/search", params={"q": "portable executable C libc"})
    assert search.status_code == 200
    slugs = [i["slug"] for i in search.json()["items"]]
    assert "cosmopolitan-libc-ape" in slugs


def test_admin_auth(client):
    denied = client.get("/admin/health")
    assert denied.status_code == 401
    ok = client.get("/admin/health", headers={"x-admin-token": "test-admin"})
    assert ok.status_code == 200
    assert "sources" in ok.json()


def test_categories(client):
    res = client.get("/categories")
    assert res.status_code == 200
    slugs = {c["slug"] for c in res.json()}
    assert {"BUILD", "WHY", "BREAK", "LANG"}.issubset(slugs)


def test_health(client):
    assert client.get("/health").json()["ok"] is True


def test_videos_and_projects(client):
    videos = client.get("/videos")
    projects = client.get("/projects")
    assert videos.status_code == 200
    assert projects.status_code == 200
    assert isinstance(videos.json(), list)
    assert isinstance(projects.json(), list)
    assert projects.json()  # demo seed includes projects


def test_stories_tag_filter(client):
    res = client.get("/stories", params={"tag": "Rust", "page_size": 5})
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert all("Rust" in (s["tags"] or []) for s in body["items"])
