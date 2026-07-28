from __future__ import annotations

from pathlib import Path

import yaml

from build_offline import write_offline_config
from build_site import write_generated_config


def write_hooked_mkdocs(root: Path) -> None:
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "mkdocs_graph_hook.py").write_text(
        "def on_config(config, **kwargs):\n    return config\n",
        encoding="utf-8",
    )
    (root / "web" / "overrides").mkdir(parents=True)
    (root / "mkdocs.yml").write_text(
        "site_name: Fixture\n"
        "site_url: https://example.invalid/Cheatsheets/\n"
        "docs_dir: build/docs\n"
        "site_dir: site\n"
        "hooks:\n"
        "  - scripts/mkdocs_graph_hook.py\n"
        "theme:\n"
        "  name: material\n"
        "  custom_dir: web/overrides\n",
        encoding="utf-8",
    )


def test_online_generated_config_resolves_hook_from_repository_root(tmp_path: Path) -> None:
    write_hooked_mkdocs(tmp_path)
    path = tmp_path / "build" / "mkdocs.generated.yml"
    write_generated_config(
        tmp_path,
        path,
        docs_dir=tmp_path / "build" / "docs",
        site_dir=tmp_path / "site",
        site_url="https://example.invalid/Cheatsheets/",
        nav=[{"Start": "index.md"}],
    )
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert parsed["hooks"] == [
        str((tmp_path / "scripts" / "mkdocs_graph_hook.py").resolve())
    ]


def test_offline_generated_config_resolves_hook_from_repository_root(tmp_path: Path) -> None:
    write_hooked_mkdocs(tmp_path)
    path = tmp_path / "build" / "mkdocs.offline.generated.yml"
    write_offline_config(
        tmp_path,
        path,
        docs_dir=tmp_path / "build" / "offline-docs",
        site_dir=tmp_path / "build" / "offline-site",
        site_url="https://example.invalid/Cheatsheets/",
        nav=[{"Start": "index.md"}],
    )
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert parsed["hooks"] == [
        str((tmp_path / "scripts" / "mkdocs_graph_hook.py").resolve())
    ]
