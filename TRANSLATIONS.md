# Translation guide

Wildfire Monitor bundles translation files for every locale currently exposed
by Home Assistant:

```text
af ar bg bn bs ca cs cy da de el en en-GB eo es es-419
et eu fa fi fy fr ga gl gsw he hi hr hu hy id is it ja ka
ko lb lt lv mk ml nb nl nn pl pt pt-BR ro ru sk sl sq sr
sr-Latn sv ta te th tr uk ur vi zh-Hans zh-Hant
```

English is the canonical source. All other translations are machine-assisted
drafts and should receive native-speaker review. They are provided to improve
accessibility, not represented as professionally certified translations.

`en-GB` and `es-419` currently match their base languages because the existing
strings need no regional override. `gsw` temporarily uses understandable
standard German, and `nn` needs particular attention from a Nynorsk reviewer.

## Safety glossary

Reviewers should preserve these distinctions:

- **Wildfire** means an uncontrolled wildland fire, not a structure fire.
- **Containment** is the reported percentage of a fire perimeter that is
  secured. It does not mean that the fire is extinguished.
- **Level 1 — Ready** means prepare.
- **Level 2 — Set** means be ready to evacuate.
- **Level 3 — Go** means evacuate now.
- **Advisory**, **warning**, **order**, and **immediate** are separate
  evacuation statuses and must retain their increasing urgency.
- `NIFC`, `NWS`, and the product name `Wildfire Monitor` must not be
  translated or transliterated.

Wildfire Monitor remains an awareness aid, not an emergency notification
system. Translations must not weaken that safety meaning.

## Contributing a review

1. Edit only `custom_components/wildfire_monitor/translations/<locale>.json`.
2. Keep every JSON key identical to `translations/en.json`.
3. Review the complete file, especially evacuation levels and statuses.
4. Run:

   ```text
   python -m pytest tests/test_translations.py
   python -m ruff check .
   python -m ruff format --check .
   ```

5. In the pull request, state that a fluent or native speaker reviewed the
   locale and note any regional language choice.
