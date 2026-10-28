# Contributing to Ajazz Linux

Ajazz Linux is an independent compatibility utility in early development. Read the [README](README.md), [validation limits](docs/VALIDATION.md) and [format compatibility](docs/reference/FORMAT_COMPATIBILITY.md) before proposing changes.

## Reports and proposals

Use the issue templates for bugs, feature proposals or optional hardware validation when the repository is hosted. Include the Ajazz Linux version/commit, Python and Qt versions, OS/session type, connection type and whether the result came from demo mode or a real device. Give reproducible steps and expected/actual behavior. Remove serial numbers, usernames, private paths and macro contents you do not want published. Follow [SECURITY.md](SECURITY.md) for vulnerabilities.

Check existing issues first. For a large behavior or protocol change, explain the evidence and proposed interface before implementing it. Do not claim broad Linux or device support from simulator results.

## Development

From the repository root on Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . build
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m build
sh ./run-vela --demo
```

On Windows, use `.venv\Scripts\python.exe` and `run-vela.cmd --demo`; see the README. For code changes, add focused tests for observable behavior and run the affected tests; run the full suite before requesting review. Documentation-only changes need link/command and spelling checks, not new application tests. Do not add a formatter or test dependency without a concrete need.

## Implementation boundaries

- Write original code and assets. Do not submit vendor binaries, extracted artwork, decompiled source or recovered implementation code. Behavioral observations, protocol facts and independently calculated vectors must cite their evidence and distinguish UNKNOWNs.
- Keep the core free of Qt imports. Preserve the real/simulator service contract and the explicit draft/Apply boundary.
- Do not add automatic device writes, firmware flashing, global input capture or unconfirmed protocol guesses. Hardware tests are optional and must be explicitly initiated by the person testing; normal automated tests use fake transports or the simulator.
- Keep file parsing bounded and native saves atomic. Reject unsupported or lossy conversions with an explanation.
- Describe limits honestly: configured CI is not a passing run, and successful reads do not validate writes or playback.

## Pull requests

Keep each change focused. Explain the problem, resulting behavior, evidence and exact checks run. Include a screenshot for material UI changes, using demo data where possible. Do not commit local workspaces, raw device captures containing private data, credentials, virtual environments or build artifacts. Review [third-party notices](THIRD_PARTY_NOTICES.md) when changing dependencies.

Contributions must be yours to share under the project's [MIT license](LICENSE). Existing dependency licenses remain separate. Follow the [code of conduct](CODE_OF_CONDUCT.md).
