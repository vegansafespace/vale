# Vale

Vale is a specialized Discord bot designed to automate community management, voice channel organization, and member onboarding for the [Vegan Safespace](https://vegansafe.space) community.

## Setup

1. Install [Python 3](https://www.python.org/downloads/).
2. Install [uv](https://docs.astral.sh/uv/).
3. Install dependencies via `uv sync`.
4. Copy `.env.dist` to `.env` and fill in the values.
    - View contents of `.env.dist` for more information.
5. Run the `src/main.py` script via `uv run python -m src.main`.

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
| `/config set application-category`                 | Slash               | Team role        | Sets the application category ID to the current channel’s category.                                             | Run in a text channel inside the desired category.                   |
| `/config set private-channels-category`            | Slash               | Team role        | Sets the private channels category ID to the current channel’s category.                                        | Run in a text channel inside the desired category.                   |
| `/config set voice-hub-category`                   | Slash               | Team role        | Sets the Voice Hub category ID to the current channel’s category.                                               | Run in a text channel inside the desired category.                   |
| `/config set voice-category`                       | Slash               | Team role        | Sets the Voice category ID to the current channel’s category.                                                   | Run in a text channel inside the desired category.                   |
| `/config set application-voice-waiting-channel`    | Slash               | Team role        | Sets the application voice waiting channel ID to the current channel.                                           | Run in the intended channel (see note below).                        |
| `/config set voice-hub-move-me-channel`            | Slash               | Team role        | Sets the Voice Hub “move me” channel ID to the current channel.                                                 | Run in the intended channel (see note below).                        |
| `/config set voice-hub-create-channel`             | Slash               | Team role        | Sets the Voice Hub “create” channel ID to the current channel.                                                  | Run in the intended channel (see note below).                        |
| `/config set application-ping-channel`             | Slash               | Team role        | Sets the application ping channel ID to the current channel.                                                    | Text channel.                                                        |
| `/config set reports-channel`                      | Slash               | Team role        | Sets the reports channel ID to the current channel.                                                             | Text channel.                                                        |
| `/config set role-justification-channel`           | Slash               | Team role        | Sets the role justification channel ID to the current channel.                                                  | Text channel.                                                        |
| `/config set team-bans-channel`                    | Slash               | Team role        | Sets the team bans channel ID to the current channel.                                                           | Text channel.                                                        |
| `/config set team-applications-channel`            | Slash               | Team role        | Sets the team applications channel ID to the current channel.                                                   | Text channel.                                                        |
| `/config set main-chat-channel`                    | Slash               | Team role        | Sets the main chat channel ID to the current channel.                                                           | Text channel.                                                        |
| `/config set non-vegan-main-chat-channel`          | Slash               | Team role        | Sets the non-vegan main chat channel ID to the current channel.                                                 | Text channel.                                                        |

Note on voice-related configuration commands:
- Some settings expect a voice channel (e.g., application waiting, move-me, create). Run the command in the exact channel or consider updating the helper to read the user’s current voice channel ID.

---

Made with ❤️ by the team of [Vegan Safespace](https://vegansafe.space).
