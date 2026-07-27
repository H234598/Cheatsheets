from __future__ import annotations

from callouts import convert_obsidian_callouts_for_web


def test_converts_all_representative_types_and_fold_states() -> None:
    source = (
        "> [!abstract] Kurz\n> Zusammenfassung.\n\n"
        "> [!tip]+ Offen\n> Tipp.\n\n"
        "> [!danger]- Geschlossen\n> Vorsicht.\n\n"
        "> [!evidence]\n> Quelle.\n"
    )
    converted = convert_obsidian_callouts_for_web(source)
    assert '!!! abstract "Kurz"\n    Zusammenfassung.\n' in converted
    assert '???+ tip "Offen"\n    Tipp.\n' in converted
    assert '??? danger "Geschlossen"\n    Vorsicht.\n' in converted
    assert '!!! evidence "Evidenz"\n    Quelle.\n' in converted


def test_preserves_nested_blockquote_content() -> None:
    source = "> [!note] Verschachtelt\n> > Innere Quote\n> Fortsetzung\n"
    assert convert_obsidian_callouts_for_web(source) == (
        '!!! note "Verschachtelt"\n'
        "    > Innere Quote\n"
        "    Fortsetzung\n"
    )


def test_callouts_inside_fence_and_unknown_types_remain_literal() -> None:
    source = (
        "````markdown\n> [!danger] Beispiel\n> Nicht konvertieren.\n````\n\n"
        "> [!custom] Unbekannt\n> Bleibt.\n"
    )
    converted = convert_obsidian_callouts_for_web(source)
    assert converted == source


def test_titles_are_escaped_for_markdown_admonition() -> None:
    source = '> [!warning] Pfad "C:\\Temp"\n> Prüfen.\n'
    converted = convert_obsidian_callouts_for_web(source)
    assert converted.startswith('!!! warning "Pfad \\"C:\\\\Temp\\""\n')
