# scaffold

Meta/template repository: the language-agnostic baseline (licensing, governance,
documentation, contribution workflow) that new personal projects start from.
Everything here is documentation or configuration — there is no code to build,
test, or run.

This file is the single source of truth for agent instructions, as prescribed
by [docs/AI-AGENTS.md](docs/AI-AGENTS.md); `CLAUDE.md` is a pointer to it.

## Commands

- There is no build, test, or lint pipeline. Validation is manual: check that
  Markdown renders correctly and that YAML files (`.github/*.yml`) stay parseable.

## Conventions

- Commits: Conventional Commits — see [docs/COMMIT-CONVENTION.md](docs/COMMIT-CONVENTION.md).
- Branching: trunk-based — see [docs/BRANCHING-STRATEGY.md](docs/BRANCHING-STRATEGY.md)
  and [ADR 0001](docs/adr/0001-trunk-based-development.md).
- All content (docs, comments, commit messages, file names) is written in
  English, no exceptions.
- Per-project customization points use the placeholders `<PROJECT_NAME>`,
  `<OWNER_HANDLE>`, `<SECURITY_CONTACT_EMAIL>`, `<CONTACT_EMAIL>`, `<YEAR>`,
  `<COPYRIGHT_HOLDER>`, and `[TO BE FILLED IN]` — reuse them, don't invent new ones.

## Boundaries

- Never commit directly to `main`; every change goes through a pull request.
- `licenses/MIT.txt`, `licenses/APACHE-2.0.txt`, and the body of
  `CODE_OF_CONDUCT.md` are canonical third-party texts: never reword them
  (placeholders and the top note in the code of conduct are the only local parts).
- Keep this repo language-agnostic: no language-specific tooling, manifests, or
  CI — that boundary is documented in the README and is deliberate.
- When adding, renaming, or removing files, update the structure tree in
  `README.md` in the same pull request.
