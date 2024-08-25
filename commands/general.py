import random
from discord.ext import commands
import discord
from .currency import user_found, check_chips, check_aura

class General(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name = 'about')
    async def about(self,ctx):
        embedVar = discord.Embed(title="Commands for BonBonBot", description="Here's a list of all the available commands:", color=0x552583)

        # General Commands
        embedVar.add_field(name="**General**", value=":information_source: **=detailedabout** - Discover commands\n:wave: **=hello** - Get a friendly greeting from BonBon\n:identification_card: **=pr** - View your BonBonBot profile\n:8ball: **=fortune** - ask bonbon a yes or no question", inline=True)

        # Aura and Chips Commands
        embedVar.add_field(name="**Aura and Chips**", value=":sparkles: **=aura** - Check your aura\n:coin: **=chips** - Check your chips\n:gift: **=daily** - Get daily chips\n:arrows_counterclockwise: **=ca** - Aura to chips\n:arrows_clockwise: **=cc** - Chips to aura\n:game_die: **=gambleaura** - Gamble aura\n:trophy: **=ranking** - Aura leaderboard", inline=True)

        # Games
        embedVar.add_field(name="**Games**", value=":fist: **=playRPS** - Start Rock Paper Scissors (add bet)\n:raised_hand: **=joinRPS** - Join ongoing Rock Paper Scissors\n:question: **=trivia** - Trivia info\n:black_joker: **=bj** - Blackjack (add bet)\n:slot_machine: **=slots** - Slots (add bet)", inline=True)

        await ctx.send(embed=embedVar)


    @commands.command(name='detailedabout')
    async def detailedabout(self,ctx):
        embedVar = discord.Embed(title="Commands for BonBonBot", description="Here's a list of all the available commands:", color=0x552583)

        # General Commands
        embedVar.add_field(name="**General**", value="\u200b", inline=False)   
        embedVar.add_field(name=":information_source: **=about**", value="Discover commands", inline=True)
        embedVar.add_field(name=":wave: **=hello**", value="Get a friendly greeting from BonBon", inline=True)
        embedVar.add_field(name=":identification_card: **=pr**", value="view your profile for BonBonBot", inline=True)
        embedVar.add_field(name=":8ball: **=fortune**", value="ask Bonbon a yes or no question", inline=True)

    # Aura and Chips Commands
        embedVar.add_field(name="\u200b", value="\u200b", inline=False)
        embedVar.add_field(name="**Aura and Chips**", value="\u200b", inline=False)
        embedVar.add_field(name=":sparkles: **=aura**", value="Check your current aura value or get your original aura reading", inline=True)
        embedVar.add_field(name=":coin: **=chips**", value="Check your balance of gambling chips, currency used for all minigames", inline=True)
        embedVar.add_field(name=":gift: **=daily**", value="Get your daily allowance of gambling chips, 500 each day", inline=True)
        embedVar.add_field(name=":arrows_counterclockwise: **=ca**", value="Convert your aura to chips (1 aura = 10 chips)", inline=True)
        embedVar.add_field(name=":arrows_clockwise: **=cc**", value="Convert your chips to aura (10 chips = 1 aura, full aura points only)", inline=True)
        embedVar.add_field(name=":game_die: **=gambleaura**", value="Get a chance at increasing or decreasing your aura", inline=True)
        embedVar.add_field(name=":trophy: **=ranking**", value="Get the leaderboard of users' aura", inline=True)

    # Games
        embedVar.add_field(name="\u200b", value="\u200b", inline=False)
        embedVar.add_field(name="**Games**", value="\u200b", inline=False)
        embedVar.add_field(name=":fist: **=playRPS**", value="Rock Paper Scissors game, command to start the game (one at a time). Add a wager amount if you would like", inline=True)
        embedVar.add_field(name=":raised_hand: **=joinRPS**", value="Join the Rock Paper Scissors game as the opponent, must match the wager of the host", inline=True)
        embedVar.add_field(name=":question: **=trivia**", value="Use `=abouttrivia` for more information about the trivia game", inline=True)
        embedVar.add_field(name=":black_joker: **=bj**", value="Blackjack game under normal rules, play against the dealer to be the closest to 21, add your bet value after the command. Add a wager amount if you would like", inline=True)
        embedVar.add_field(name=":slot_machine: **=slots**", value="Take a roll on the slot machine, match a row of symbols to multiply your bet", inline=True)

        await ctx.send(embed=embedVar)


    @commands.command(name='hello')
    async def hello(self,ctx):
        username = ctx.author.name  # Get the username of the person who invoked the command
        if str(username) == ".enyo." or str(username) == "aloosa" or str(username) == "josh._._.":
            response = f'https://tenor.com/view/coroca-breaking-bad-gif-20039378'
        else:
            response = f'hello, {username}!!!'
        await ctx.send(response)


    @commands.command(name='pr')
    async def pr(self,ctx):
        username = ctx.author.name
        user_avatar_url = ctx.author.avatar.url  # Get the user's profile picture URL
    
        if user_found('users.json', username):
            aura_value = check_aura('users.json', username)
            chips_value = check_chips('users.json', username)
        
            # Create an embed for the user's profile
            embedVar = discord.Embed(title=f"{username}'s Profile", color=0x552583)
            embedVar.set_thumbnail(url=user_avatar_url)  # Set the user's profile picture
            embedVar.add_field(name="Name", value=username, inline=True)
            embedVar.add_field(name="Aura", value=aura_value, inline=True)
            embedVar.add_field(name="Chips", value=chips_value, inline=True)
        
            await ctx.send(embed=embedVar)
        else:
            await ctx.send(f'{ctx.author.mention}, you need to get your initial aura by typing `=aura` first.')


    @commands.command(name='fortune')
    async def fortune(self, ctx, question: str=""):
        if question == "":
            await ctx.send('Enter a yes or no question with the command')
        else:
            fortune = ['yes', 'most likely', 'without a doubt', 'Dont count on it', 'very doubtful', 'no', 'certainly not', 'maybe', 'possibly']
            msg = fortune[random.randint(0, 8)]
            await ctx.send(msg)

async def setup(client):
    await client.add_cog(General(client))