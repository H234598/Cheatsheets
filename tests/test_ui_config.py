from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import manifest_row, write_manifest, write_page
from content_index import build_content_index
from ui_config import UIConfigError, load_page_id_aliases, write_ui_data


def make_repository(root: Path) -> tuple[object, str]:
    page = write_page(
        root,
        "01-Test/Alpha.md",
        title="Alpha",
        body="# Alpha\n\nInhalt.\n",
    )
    write_page(
        root,
        "01-Test/INDEX.md",
        title="Test – Kategorienindex",
        page_type="index",
        body="# Test\n\n## Seiten\n\n- [[01-Test/Alpha|Alpha]]\n",
        extra="pages: 1\n",
    )
    write_manifest(root, [manifest_row(1, "Test", "Alpha", page, root)])
    index = build_content_index(root)
    return index, index.reference_pages[0].page_id


def write_aliases(root: Path, aliases: dict[str, str]) -> Path:
    path = root / "config" / "page-id-aliases.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"aliases": aliases, "schema_version": 1},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def test_valid_alias_targets_current_reference_page(tmp_path: Path) -> None:
    index, current_id = make_repository(tmp_path)
    old_id = "p_0000000000000000"
    write_aliases(tmp_path, {old_id: current_id})

    payload = load_page_id_aliases(tmp_path, index)

    assert payload == {
        "aliases": {old_id: current_id},
        "schema_version": 1,
    }


def test_alias_target_must_exist_in_current_inventory(tmp_path: Path) -> None:
    index, _ = make_repository(tmp_path)
    write_aliases(
        tmp_path,
        {"p_0000000000000000": "p_1111111111111111"},
    )

    with pytest.raises(UIConfigError, match="Migrationsziel existiert nicht"):
        load_page_id_aliases(tmp_path, index)


def test_current_page_id_cannot_be_marked_as_obsolete(tmp_path: Path) -> None:
    index, current_id = make_repository(tmp_path)
    write_aliases(tmp_path, {current_id: "p_1111111111111111"})

    with pytest.raises(UIConfigError, match="Aktuelle Page-ID"):
        load_page_id_aliases(tmp_path, index)


def test_alias_register_rejects_symlink_before_reading_target(tmp_path: Path) -> None:
    index, _ = make_repository(tmp_path)
    external = tmp_path.parent / "external-ui-secret.json"
    external.write_text(
        '{"schema_version": 1, "aliases": {}, "secret": "DO_NOT_LEAK"}\n',
        encoding="utf-8",
    )
    link = tmp_path / "config" / "page-id-aliases.json"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden auf dieser Plattform nicht unterstützt: {exc}")

    with pytest.raises(UIConfigError, match="Symbolischer Link") as captured:
        load_page_id_aliases(tmp_path, index)
    assert "DO_NOT_LEAK" not in str(captured.value)


def test_ui_data_is_written_deterministically(tmp_path: Path) -> None:
    index, current_id = make_repository(tmp_path)
    old_id = "p_0000000000000000"
    write_aliases(tmp_path, {old_id: current_id})
    staging = tmp_path / "build" / "docs"

    target = write_ui_data(staging, tmp_path, index)

    assert target == staging / "data" / "page-id-aliases.json"
    assert target.read_text(encoding="utf-8") == (
        '{\n  "aliases": {\n'
        f'    "{old_id}": "{current_id}"\n'
        '  },\n  "schema_version": 1\n}\n'
    )
