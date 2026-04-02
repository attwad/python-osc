Thanks for contributing to this package!

Before sending a PR, please make sure you checked the [python test workflow](.github/workflows/python-test.yml) and ran it locally, either using [act](https://nektosact.com) or by executing the workflow actions yourself.

TL;DR:
-  Format and lint all code with [ruff](https://docs.astral.sh/ruff/) (use `uv run ruff format .` and `uv run ruff check .`)
-  Provide type annotations with mypy (`uv run mypy pythonosc examples`)
-  Write and run tests with pytest (`uv run pytest`)
-  Use [uv](https://docs.astral.sh/uv/) for package management and environment isolation
-  If you're adding a new feature, mention it in the [CHANGELOG.md](CHANGELOG.md) file under the _Unreleased_ section

Please only send the PR once all of the above is done, thanks!