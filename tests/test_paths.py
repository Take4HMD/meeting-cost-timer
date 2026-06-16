import sys

from app.utils.paths import project_path, project_root, resource_path


def test_project_path_resolves_from_project_root():
    assert project_path("config", "app_settings.json") == (
        project_root() / "config" / "app_settings.json"
    )


def test_resource_path_uses_meipass_when_available(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert resource_path("app/ui/main_menu.ui") == tmp_path / "app/ui/main_menu.ui"
