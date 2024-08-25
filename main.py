from typing import Final
import discord
from discord.ext import commands
from commands.games import determine_winner
import config
import os
from dotenv import load_dotenv


load_dotenv()

TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")


intents: discord.Intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(command_prefix='=', intents=intents)

async def load_cogs():
    for filename in os.listdir('./commands'):
        if filename.endswith('.py'):
            try:
                await client.load_extension(f'commands.{filename[:-3]}')
                print(f'Loaded extension: {filename}')
            except Exception as e:
                print(f'Failed to load extension {filename}: {e}')

@client.event
async def on_message(message: discord.Message):
    await client.process_commands(message)

    if message.author == client.user:
        return

    if message.channel.type == discord.ChannelType.private:
        for member in config.joined_users:
            if message.author.name == member.name:
                print(member.name)
                answer = message.content.lower()
                if answer not in ['rock', 'paper', 'scissors']:
                    await message.author.send("This is not a valid answer, your options are Rock, Paper or Scissors")
                    return
                config.choices[message.author] = answer
                print(f"{message.author.name} chose {answer}")
                await message.author.send(f"Your answer '{answer}' has been recorded.")

                if len(config.choices) == 2:
                    config.game_event.set()
                    player1, player2 = list(config.choices.keys())
                    choice1, choice2 = config.choices[player1], config.choices[player2]
                    result = determine_winner(player1, choice1, player2, choice2)
                    await config.game_channel.send(f"{player1.mention} chose {choice1}.  {player2.mention} chose {choice2}.\n\n{result}")
                    config.choices.clear()  # Clear choices for the next game
                    config.joined_users.clear()
                    config.game_in_progress = False  # End the current game
                    config.wager = 0
                    config.game_channel = None
                    return

@client.event
async def on_ready():
    print(f'{client.user} is now running!')
    await load_cogs()

def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()