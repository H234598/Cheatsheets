from __future__ import annotations

from pathlib import Path

import pytest

from validate_security import analyze_security, fingerprint, visible_markdown


def write_configs(root: Path, *, allowances: str = "") -> None:
    config = root / "config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "html-allowlist.yaml").write_text(
        "schema_version: 1\n\n"
        "allowed_tags:\n"
        "  - br\n"
        "  - details\n"
        "  - kbd\n"
        "  - mark\n"
        "  - sub\n"
        "  - summary\n"
        "  - sup\n\n"
        "allowed_attributes:\n"
        "  - aria-describedby\n"
        "  - aria-label\n"
        "  - class\n"
        "  - id\n"
        "  - open\n"
        "  - title\n",
        encoding="utf-8",
    )
    (config / "secret-allowlist.yaml").write_text(
        "schema_version: 1\n\nallow:\n" + (allowances or "  []\n"),
        encoding="utf-8",
    )


def write_markdown(root: Path, body: str, name: str = "Alpha.md") -> Path:
    path = root / "01-Test" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: Alpha\ntype: reference\nstatus: fertig\ntags: [test]\n---\n"
        + body,
        encoding="utf-8",
    )
    return path


def issue_codes(root: Path) -> set[str]:
    return {issue.code for issue in analyze_security(root)}


def test_active_html_outside_fence_is_blocked(tmp_path: Path) -> None:
    write_configs(tmp_path)
    write_markdown(tmp_path, "# Alpha\n\n<script>alert(1)</script>\n")

    assert "SC010" in issue_codes(tmp_path)


def test_html_teaching_example_inside_fence_is_not_treated_as_active(tmp_path: Path) -> None:
    write_configs(tmp_path)
    write_markdown(
        tmp_path,
        "# Alpha\n\n```html\n<script>alert(1)</script>\n<img src=\"https://example.invalid/a.png\">\n```\n",
    )

    codes = issue_codes(tmp_path)
    assert "SC010" not in codes
    assert "SC015" not in codes


def test_high_confidence_token_is_detected_even_inside_teaching_fence(tmp_path: Path) -> None:
    write_configs(tmp_path)
    token = "ghp_" + "A" * 36
    write_markdown(tmp_path, f"# Alpha\n\n```text\n{token}\n```\n")

    issues = analyze_security(tmp_path)

    assert any(issue.code == "SC001" and issue.rule == "github-token" for issue in issues)
    assert token not in "\n".join(issue.message for issue in issues)


def test_exact_path_and_hash_allowance_suppresses_only_matching_secret(
    tmp_path: Path,
) -> None:
    token = "ghp_" + "B" * 36
    digest = fingerprint(token)
    allowance = (
        "  - rule: github-token\n"
        "    path: 01-Test/Alpha.md\n"
        f"    match_sha256: {digest}\n"
        "    reason: Deterministische Testfixture\n"
    )
    write_configs(tmp_path, allowances=allowance)
    write_markdown(tmp_path, f"# Alpha\n\n```text\n{token}\n```\n")

    assert "SC001" not in issue_codes(tmp_path)


def test_external_markdown_image_and_event_handler_are_blocked(tmp_path: Path) -> None:
    write_configs(tmp_path)
    write_markdown(
        tmp_path,
        "# Alpha\n\n![Extern](https://example.invalid/a.png)\n\n"
        "<details onclick=\"alert(1)\"><summary>Mehr</summary></details>\n",
    )

    codes = issue_codes(tmp_path)
    assert "SC020" in codes
    assert "SC012" in codes


def test_allowlisted_details_markup_is_clean(tmp_path: Path) -> None:
    write_configs(tmp_path)
    write_markdown(
        tmp_path,
        "# Alpha\n\n<details open><summary title=\"Mehr\">Inhalt</summary></details>\n",
    )

    assert analyze_security(tmp_path) == []


def test_autolinks_inline_code_and_comments_are_not_raw_html(tmp_path: Path) -> None:
    write_configs(tmp_path)
    write_markdown(
        tmp_path,
        "# Alpha\n\n<https://example.invalid/path>\n\n"
        "`<script>alert(1)</script>`\n\n"
        "<!-- <script>alert(1)</script> -->\n",
    )

    assert analyze_security(tmp_path) == []


def test_visible_markdown_preserves_line_numbers_while_masking_protected_regions() -> None:
    text = (
        "---\ntitle: Fixture\n---\n"
        "# Sichtbar\n"
        "```html\n<script>x</script>\n```\n"
        "<details>ok</details>\n"
    )

    visible = visible_markdown(text)

    assert visible.count("\n") == text.count("\n")
    assert "<script>" not in visible
    assert "<details>" in visible


def test_markdown_symlink_is_rejected_without_reading_external_content(
    tmp_path: Path,
) -> None:
    write_configs(tmp_path)
    external = tmp_path.parent / "external-secret.md"
    external.write_text("ghp_" + "C" * 36 + "\n", encoding="utf-8")
    link = tmp_path / "01-Test" / "Linked.md"
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.symlink_to(external)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Symlinks werden auf dieser Plattform nicht unterstützt: {exc}")

    issues = analyze_security(tmp_path)

    assert any(issue.code == "SC030" for issue in issues)
    assert not any(issue.code == "SC001" for issue in issues)
