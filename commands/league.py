import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# Load the .env file to access the API key
load_dotenv()

api_key = os.getenv('api_key')

class League(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.command(name='aboutleague')
    async def aboutleague(self, ctx):
        embedVar = discord.Embed(
            title="Commands for League of Legends", 
            description="What you can do with the League API", 
            color=0x552583
        )
        embedVar.add_field(name=":sparkles: **=rank**", value="Check your current rank", inline=True)
        await ctx.send(embed=embedVar)

    @commands.command(name='rank')
    async def rank(self, ctx, gameName: str = None, tagLine: str = None):
        if not gameName or not tagLine:
            await ctx.send("Error: You must provide both a game name and a tagline.\nUsage: `=rank <gameName> <tagLine>`")
            return
        
        await ctx.send(f"Fetching rank for {gameName}#{tagLine}...")

        puuid = await self.get_puuid(gameName, tagLine)
        if not puuid:
            await ctx.send("Error: Unable to fetch puuid for the provided game name and tagline.")
            return

        user = await self.get_summoner_by_puuid(puuid)
        if user is None:
            await ctx.send("Error: Unable to fetch summoner details.")
            return
        
        sumID = user['summonerId']
        profile_icon_id = user['profileIcon']
        

        ranked_data = await self.get_ranked_data_sumID(sumID)
        if 'error' in ranked_data:
            await ctx.send(f"Error fetching ranked data: {ranked_data['error']}")
            return
        
        profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/13.20.1/img/profileicon/{profile_icon_id}.png"
        
        embedVar = discord.Embed(
            title=f"Ranked Stats for {gameName}#{tagLine}",
            color=0x552583
        )
        embedVar.set_thumbnail(url=profile_icon_url)
        embedVar.add_field(name="**Queue Type:**", value=ranked_data['queueType'], inline=False)
        embedVar.add_field(name="**Tier:**", value=f"{ranked_data['tier']} {ranked_data['rank']}", inline=False)
        embedVar.add_field(name="**LP:**", value=ranked_data['leaguePoints'], inline=False)
        embedVar.add_field(name="**Wins:**", value=ranked_data['wins'], inline=False)
        embedVar.add_field(name="**Losses:**", value=ranked_data['losses'], inline=False)
        
        embedVar.set_footer(text="Data from Riot Games API")

        await ctx.send(embed=embedVar)

    async def get_puuid(self, gameName, tagLine):
        link = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={api_key}'
        response = requests.get(link)
        if response.status_code == 200:
            return response.json().get('puuid')
        return None

    async def get_summoner_by_puuid(self, puuid, region='americas'):
        matches = await self.get_matchhistory(puuid=puuid, region=region, count=1)
        if matches:
            firstmatch = matches[0]
            match_data = await self.get_matchData(match_id=firstmatch)
            for participant in match_data['info']['participants']:
                if participant['puuid'] == puuid:
                    return participant
        return None

    async def get_matchhistory(self, puuid, region='americas', start=0, count=20):
        link = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}&api_key={api_key}'
        response = requests.get(link)
        if response.status_code == 200:
            return response.json()
        return None

    async def get_matchData(self, match_id):
        link = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={api_key}'
        response = requests.get(link)
        if response.status_code == 200:
            return response.json()
        return None

    async def get_ranked_data_sumID(self, sumID, region='na1'):
        link = f'https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{sumID}?api_key={api_key}'
        response = requests.get(link)
        if response.status_code == 200:
            ranked_data = response.json()
            if ranked_data:  # Check if the ranked data is not empty
                return ranked_data[0]
            else:
                return {'error': 'No ranked data available for this summoner.'}
        return {'error': 'Unable to fetch ranked data'}

async def setup(client):
    await client.add_cog(League(client))