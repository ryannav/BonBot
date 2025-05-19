from discord.ext import commands, tasks
import discord
import yt_dlp
import asyncio
import os

FFMPEG_OPTIONS = {'options': '-vn'}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ffmpeg_path = "ffmpeg" #FOR IF YOU ARE ON WINDOWS  os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")

class Musica(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.idle_timer = None

    def same_voice_channel(self, ctx):
        return ctx.author.voice and ctx.voice_client and ctx.author.voice.channel == ctx.voice_client.channel

    async def start_idle_timer(self, ctx):
        if self.idle_timer:
            self.idle_timer.cancel()

        async def timer():
            await asyncio.sleep(600)  # 10 minutes
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.send("Idle for 10 minutes. Disconnecting.")
                await ctx.voice_client.disconnect()
                self.queue.clear()

        self.idle_timer = asyncio.create_task(timer())

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You are not in a voice channel.")

        if ctx.voice_client and ctx.voice_client.channel != voice_channel:
            return await ctx.send("You must be in the same voice channel as the bot.")

        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                await ctx.send(f'Added to queue: **{title}**')

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        if self.queue:
            url, title = self.queue.pop(0)
            source = discord.FFmpegOpusAudio(url, **FFMPEG_OPTIONS, executable=ffmpeg_path)
            ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
            await ctx.send(f'Now playing **{title}**')
        else:
            await self.start_idle_timer(ctx)

    @commands.command()
    async def skip(self, ctx):
        if not self.same_voice_channel(ctx):
            return await ctx.send("You must be in the same voice channel as the bot to skip.")
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped")

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        if not self.queue:
            return await ctx.send("The queue is currently empty.")
        queue_list = "\n".join([f"{idx+1}. {title}" for idx, (_, title) in enumerate(self.queue)])
        await ctx.send(f"**Current Queue:**\n{queue_list}")

    @commands.command(aliases=['dc', 'disconnect', 'stop'])
    async def leave(self, ctx):
        if not self.same_voice_channel(ctx):
            return await ctx.send("You must be in the same voice channel as the bot to make it leave.")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            if self.idle_timer:
                self.idle_timer.cancel()
            await ctx.send("Disconnected and cleared the queue.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

async def setup(client):
    await client.add_cog(Musica(client))
