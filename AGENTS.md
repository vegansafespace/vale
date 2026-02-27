# AGENTS.md for Vale Bot

## Dev environment tips
- Use `uv sync` to install dependencies and keep your environment up to date.
- Run the bot locally using `uv run python -m src.main`.
- This project uses **Dependency Injection** via `dependency-injector`. Most components are wired in `src/containers.py` and injected into cogs and services using the `@inject` decorator and `Provide` markers.
- When adding a new service or component, register it in `src/containers.py` to make it available for injection.

## Project Structure
- `src/main.py`: The entry point of the bot.
- `src/vale.py`: Core bot class inheriting from `commands.Bot`.
- `src/cogs/`: Contains modular extensions (Cogs) for Discord commands and events (e.g., `leveling_utils.py`).
- `src/components/`: Business logic and services (e.g., application flow, voice management, leveling system).
- `src/modals/`: Discord UI modals for user input.
- `src/containers.py`: Dependency injection configuration.
- `src/helpers/`: Utility functions and helpers (environment, database, `config_keys.py`).
- `CHANGELOG.md`: Tracks all notable changes to the project.
- `README.md`: Contains general bot information and command list.
- `src/logger.py`: Logging configuration.

## Testing instructions
- **Location**: All tests must be placed in the `tests/` directory.
- **Async Tests**: This project uses `pytest-asyncio`. Mark async tests with `@pytest.mark.asyncio`.
- **Mocking**: Use `unittest.mock` (`AsyncMock` for async methods) to mock dependencies like `ConfigurationService` or `Motor` collections.
- **CI**: Every PR must pass the GitHub Actions CI (runs on Python 3.9 using `uv`).
- **Feature changes**: Ensure to update `README.md` with any new commands or logic changes.
- **Run all tests**: `uv run pytest`
- **Run specific test**: `uv run pytest tests/components/test_leveling_service.py`
- **Add or update tests**: Always add or update tests for any logic changes.

## PR instructions
- **Conventional Commits**: We use [Conventional Commits](https://www.conventionalcommits.org/) for automated releases via `release-please`. Ensure your commit messages follow the format (e.g., `feat: add new feature`, `fix: resolve bug`).
- **Changelog**: Release-please automatically updates `CHANGELOG.md` based on your commit messages.
- Title format: `[<scope>] <Title>` (e.g., `[cogs] add user utilities`).
- Always verify your changes locally before committing.
- Ensure that any new dependencies are added to `pyproject.toml` using `uv add`.
