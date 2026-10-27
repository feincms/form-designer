# Agent instructions

## Tests

Run the test suite with tox, e.g. `tox -e py313-dj52`. Pass test labels as
positional arguments to run a subset: `tox -e py313-dj52 -- testapp.test_forms`.

Tests live in `tests/testapp/` and use Django's `TestCase`. The test project
uses FeinCMS pages (`FormContent`); migrations for FeinCMS's `page` app live in
`tests/testapp/migrate/page/`.

CI (`.github/workflows/tests.yml`) runs every `py<version>-*` tox environment
for each Python version in its matrix, so keep the CI matrix, the tox envlist
and the `pyproject.toml` classifiers in sync.

## Conventions

- Pre-commit hooks (ruff check, ruff format, django-upgrade, …) run on commit;
  ruff enforces pep8-naming, so local variables must be lowercase.
- Changes to model fields (including `help_text` and `verbose_name`) need a
  migration in `form_designer/migrations/`.
- Field types are configured in `form_designer/default_field_types.py`;
  settings and field types are documented in `README.rst`.
- Translations live in `form_designer/locale/`. After `makemessages`, check
  for `#, fuzzy` entries and stale `#| msgid` matches before compiling the
  `.mo` files.
- Add user-facing changes to `CHANGELOG.rst` under "Next version". Separate
  version sections with one blank line.

## Commits

- Commit feature by feature: one commit per fix or feature, each including
  its tests and changelog entry.
- No attribution lines (no `Co-Authored-By` etc.).
- Keep commit messages short and don't repeat what the diff or changelog
  already says.
