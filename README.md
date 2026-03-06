# Vale

Vale is a specialized Discord bot designed to automate community management, voice channel organization, and member onboarding for the [Vegan Safespace](https://vegansafe.space) community.

## Key Features

- **Dynamic Voice Management**: Automatically creates and removes voice channels based on user demand, keeping the server organized.
- **Member Onboarding**: Manages a structured application process with dedicated waiting rooms and interview channels.
- **Automated Role Assignment**: Ensures new members receive appropriate roles immediately upon joining.
- **Moderation Tools**: Streamlines reporting and banning processes for the staff team.
- **Leveling System**: Reward users for their contributions with XP and ranks. Users can earn XP through text messages and voice activity (levels 0-60 by default, fully configurable).
- **Automated Voice XP**: Periodically grants XP to users active in voice channels, with configurable intervals and rewards.
- **Task Automation**: Periodically cleans up inactive channels and ensures data consistency across the server.

## Project Structure

- `src/main.py`: The entry point of the bot.
- `src/vale.py`: Core bot class inheriting from `commands.Bot`.
- `src/cogs/`: Contains modular extensions (Cogs):
    - `config_utils.py`: Bot configuration management (slash commands).
    - `events.py`: Central event orchestrator (joins, voice updates, XP gain).
    - `leveling_utils.py`: Leveling system commands (rank, configuration).
    - `tasks.py`: Background automation (periodic role checks).
    - `team_utils.py`: Staff tools (moderation, onboarding, logging).
    - `user_utils.py`: Member utilities (reporting, application process).
- `src/components/`: Business logic for specific features:
    - `application.py` & `application_service.py`: Onboarding flow logic.
    - `configuration_service.py`: Database-backed configuration management.
    - `leveling_service.py`: Leveling logic and XP management.
    - `voice_category.py` & `voice_hub.py`: Dynamic voice channel management.
- `src/modals/`: Discord UI modals for user input (applications, diagnostics).
- `src/containers.py`: Dependency injection configuration using `dependency_injector`.
- `src/helpers/`:
    - `env.py`: Environment variable management.
    - `config_keys.py`: Configuration key constants.
    - `mongodb.py`: Database connection helper.
- `src/logger.py`: Logging configuration.

## Setup

1. Install [Python 3](https://www.python.org/downloads/).
2. Install [uv](https://docs.astral.sh/uv/).
3. Install dependencies via `uv sync`.
4. Copy `.env.dist` to `.env` and fill in the values.
    - View contents of `.env.dist` for more information.
5. Run the `src/main.py` script via `uv run python -m src.main`.

## Testing

Run the test suite using `pytest` via `uv`:

```bash
uv run pytest
```

Individual tests or folders can be targeted:

```bash
uv run pytest tests/components/test_leveling_service.py
```

Tests are automatically run on GitHub for every Pull Request.

## Leveling

Vale includes a custom leveling system to reward active community members for both text and voice participation.

### XP Formula

The system uses a cubic progression formula, behaving like the Mee6 bot:

```
XP = 5 * (lvl^2) + (50 * lvl) + 100
```

Where:
- `lvl` is the current level.
- The result is the XP required to reach the **next** level.

The total XP required for level $N$ is the sum of XP required for all previous levels:
$\sum_{i=0}^{N-1} (5i^2 + 50i + 100)$.

### Text XP

By default, users receive **20 XP** per message with a **60-second cooldown** to prevent spam.

### Voice XP

Users also earn XP for time spent in voice channels:

- **Default interval**: 15 minutes of activity.
- **Default reward**: 5 XP per interval.
- Users must be unmuted and undeafend in a voice channel to earn XP.
- Activity is tracked periodically and XP is awarded once the configured interval is reached.

## Commands

The following commands are available. Unless noted, commands are guild-only.

| Command                                            | Type                | Permission/Role  | Description                                                                                                     | Notes                                                                |
|----------------------------------------------------|---------------------|------------------|-----------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| `!sync [guilds] [spec]`                            | Prefix (owner-only) | Bot owner        | Synchronize the application command tree with Discord. `spec` can be `~`, `*`, or `^` for per-guild operations. | Maintenance utility; responds in the invoking channel.               |
| `/test`                                            | Slash               | Vegan role       | Opens a simple test modal.                                                                                      | For diagnostics.                                                     |
| `/apply`                                           | Slash               | New User role    | Starts the application process and opens the application modal.                                                 | Stores application in MongoDB and notifies the team.                 |
| `/revoke-application`                              | Slash               | New User role    | Revokes your pending application.                                                                               | Notifies the team channel and removes the DB record.                 |
| Beitrittsdatum zeigen                              | Context (User)      | Vegan role       | Shows the selected member’s join date.                                                                          | Right-click a user → Apps.                                           |
| Dem Team melden                                    | Context (Message)   | Vegan role       | Reports the selected message to the team.                                                                       | Right-click a message → Apps; sends an embed to the reports channel. |
| `/ban user <user> reason <text> [delete_messages]` | Slash               | Team role        | Bans a user from the guild with an optional message deletion flag.                                              | Sends an embed to the bans channel and optionally DMs the user.      |
| `/vegan member <member> reason <text>`             | Slash               | Team role        | Assigns the Vegan role and removes onboarding roles.                                                            | Welcomes the user in the configured main chat.                       |
| `/non-vegan member <member> [reason]`              | Slash               | Team role        | Assigns the “Auf dem Weg” role and removes conflicting roles.                                                   | Welcomes the user in the configured non-vegan main chat.             |
| `/config set app-category`                         | Slash               | Team role        | Sets the application category ID to the current channel’s category.                                             | Run in a text channel inside the desired category.                   |
| `/config set private-channels-category`            | Slash               | Team role        | Sets the private channels category ID to the current channel’s category.                                        | Run in a text channel inside the desired category.                   |
| `/config set voice-hub-category`                   | Slash               | Team role        | Sets the Voice Hub category ID to the current channel’s category.                                               | Run in a text channel inside the desired category.                   |
| `/config set voice-category`                       | Slash               | Team role        | Sets the Voice category ID to the current channel’s category.                                                   | Run in a text channel inside the desired category.                   |
| `/config set app-voice-waiting`                    | Slash               | Team role        | Sets the application voice waiting channel ID to the current channel.                                           | Run in the intended channel (see note below).                        |
| `/config set voice-hub-move-me-channel`            | Slash               | Team role        | Sets the Voice Hub “move me” channel ID to the current channel.                                                 | Run in the intended channel (see note below).                        |
| `/config set voice-hub-create-channel`             | Slash               | Team role        | Sets the Voice Hub “create” channel ID to the current channel.                                                  | Run in the intended channel (see note below).                        |
| `/config set app-ping-channel`                     | Slash               | Team role        | Sets the application ping channel ID to the current channel.                                                    | Text channel.                                                        |
| `/config set reports-channel`                      | Slash               | Team role        | Sets the reports channel ID to the current channel.                                                             | Text channel.                                                        |
| `/config set role-justification-channel`           | Slash               | Team role        | Sets the role justification channel ID to the current channel.                                                  | Text channel.                                                        |
| `/config set team-bans-channel`                    | Slash               | Team role        | Sets the team bans channel ID to the current channel.                                                           | Text channel.                                                        |
| `/config set team-applications-channel`            | Slash               | Team role        | Sets the team applications channel ID to the current channel.                                                   | Text channel.                                                        |
| `/config set main-chat-channel`                    | Slash               | Team role        | Sets the main chat channel ID to the current channel.                                                           | Text channel.                                                        |
| `/config set non-vegan-main-chat-channel`          | Slash               | Team role        | Sets the non-vegan main chat channel ID to the current channel.                                                 | Text channel.                                                        |
| `/rank [member]`                                   | Slash               | Everyone         | Shows the selected member’s (or your) level, XP, progress to next level, and estimated messages remaining.      | Uses guild-configured XP per message.                                |
| `/leveling set-role <level> <role>`                | Slash               | Team role        | Sets a reward role for rank levels (multiples of 5).                                                            | Level must be a multiple of 5 and ≤ max level.                       |
| `/leveling set-max-level <level>`                  | Slash               | Team role        | Sets the maximum level cap for the leveling system.                                                             | Defaults to 60.                                                      |
| `/leveling set-xp-per-message <amount>`            | Slash               | Team role        | Sets the amount of XP awarded per message for this guild.                                                       | Default is 20 XP.                                                    |
| `/leveling set-xp-per-voice-interval <amount>`     | Slash               | Team role        | Sets the amount of XP awarded per voice activity interval.                                                       | Default is 5 XP.                                                     |
| `/leveling set-voice-interval <minutes>`           | Slash               | Team role        | Sets the duration of the voice activity interval in minutes.                                                    | Default is 15 minutes.                                               |
| `/leveling toggle-channel-exclusion [channel]`     | Slash               | Team role        | Toggles XP exclusion for the specified (or current) channel.                                                    | Useful for bot-command or spam channels.                             |
| `/leveling toggle-category-exclusion [id]`         | Slash               | Team role        | Toggles XP exclusion for all channels in the specified (or current) category.                                   | Can use category ID or current channel's category.                   |
| `/leveling list-exclusions`                        | Slash               | Team role        | Lists all excluded channels and categories.                                                                    | Helpful for auditing configuration.                                  |

Note on voice-related configuration commands:
- Some settings expect a voice channel (e.g., application waiting, move-me, create). Run the command in the exact channel or consider updating the helper to read the user’s current voice channel ID.

---

Made with ❤️ by the team of [Vegan Safespace](https://vegansafe.space).
