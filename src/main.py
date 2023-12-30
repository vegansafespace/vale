from src.containers import Container
from src.helpers.env import DISCORD_TOKEN
from src.vale import Vale

container = Container()
container.wire(modules=[__name__])


def main() -> None:
    bot: Vale = container.bot()
    bot.run(token=DISCORD_TOKEN)


if __name__ == '__main__':
    main()
