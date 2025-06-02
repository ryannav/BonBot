from discord.ext import commands, tasks
import discord
import yt_dlp
import asyncio
import os

YDL_OPTIONS = {
    'format': 'bestaudio[ext=m4a]/bestaudio/best',
    'noplaylist': True
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ffmpeg_path = "ffmpeg"  # Use "ffmpeg" if on windows os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe")


class Musica(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.idle_timer = None
        self.current_song = None

    def same_voice_channel(self, ctx):
        return ctx.author.voice and ctx.voice_client and ctx.author.voice.channel == ctx.voice_client.channel

    def make_queue_entry(self, search, title=None, thumbnail=None, url=None):
        return (search, title or search, thumbnail, url)

    async def start_idle_timer(self, ctx):
        if self.idle_timer:
            self.idle_timer.cancel()

        async def timer():
            await asyncio.sleep(600)  # 10 minutes
            if ctx.voice_client and not ctx.voice_client.is_playing():
                embed = discord.Embed(
                    title="⏰ Idle Timeout",
                    description="No music has played for 10 minutes. Disconnecting.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                await ctx.voice_client.disconnect()
                self.queue.clear()

        self.idle_timer = asyncio.create_task(timer())

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            embed = discord.Embed(
                title="⚠️ Error",
                description="You are not in a voice channel.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        if ctx.voice_client and ctx.voice_client.channel != voice_channel:
            embed = discord.Embed(
                title="⚠️ Error",
                description="You must be in the same voice channel as the bot.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        if not ctx.voice_client:
            await voice_channel.connect()

        if not ctx.voice_client.is_playing() and len(self.queue) == 0:
            async with ctx.typing():
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{search}", download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url = info['url']
                    title = info['title']
                    thumbnail = info.get('thumbnail')
                    self.queue.append(self.make_queue_entry(search, title, thumbnail, url))

                    embed = discord.Embed(
                        title="🎶 Added to Queue",
                        description=f"**{title}**",
                        color=discord.Color.blue()
                    )
                    if thumbnail:
                        embed.set_thumbnail(url=thumbnail)
                    await ctx.send(embed=embed)

            await self.play_next(ctx)
        else:
            self.queue.append(self.make_queue_entry(search))
            embed = discord.Embed(
                title="🎶 Added to Queue",
                description=f"**{search}** (will load when playing)",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)

    async def play_next(self, ctx):
        if self.queue:
            search, title, thumbnail, url = self.queue.pop(0)
            if url is None:
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(f"ytsearch:{search}", download=False)
                    if 'entries' in info:
                        info = info['entries'][0]
                    url = info['url']
                    title = info['title']
                    thumbnail = info.get('thumbnail')
            self.current_song = title

            source = discord.FFmpegOpusAudio(url, **FFMPEG_OPTIONS, executable=ffmpeg_path)
            view = PlayerControls(ctx, self)

            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{title}**",
                color=discord.Color.green()
            )
            if thumbnail:
                embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text="Use the buttons below to control playback.")
            message = await ctx.send(embed=embed, view=view)
            view.message = message

            def after_playback(error):
                if error:
                    print(f"Error in playback: {error}")
                self.client.loop.create_task(self.disable_controls_and_continue(ctx, view))

            ctx.voice_client.play(source, after=after_playback)
        else:
            self.current_song = None
            await self.start_idle_timer(ctx)

    async def disable_controls_and_continue(self, ctx, view):
        view.disable_all_buttons()
        await view.message.edit(view=view)
        await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if not self.same_voice_channel(ctx):
            embed = discord.Embed(
                title="⚠️ Error",
                description="You must be in the same voice channel as the bot to skip.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(
                title="⏭️ Skipped",
                description="The current song has been skipped.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        embed = discord.Embed(
            title="🎶 Music Queue",
            color=discord.Color.blurple()
        )

        now_playing = self.current_song if self.current_song else "Nothing is currently playing."
        embed.add_field(name="Now Playing 🎵", value=now_playing, inline=False)

        if self.queue:
            queue_list = "\n".join([
                f"{idx+1}. {title if title else search}"
                for idx, (search, title, _, _) in enumerate(self.queue)
            ])
            embed.add_field(name="Up Next ⏭️", value=queue_list, inline=False)
        else:
            embed.add_field(name="Up Next ⏭️", value="The queue is empty.", inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=['dc', 'disconnect', 'stop'])
    async def leave(self, ctx):
        if not self.same_voice_channel(ctx):
            embed = discord.Embed(
                title="⚠️ Error",
                description="You must be in the same voice channel as the bot to make it leave.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            if self.idle_timer:
                self.idle_timer.cancel()
            embed = discord.Embed(
                title="👋 Disconnected",
                description="Disconnected from the voice channel and cleared the queue.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ Error",
                description="I'm not connected to a voice channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)


async def setup(client):
    await client.add_cog(Musica(client))


class PlayerControls(discord.ui.View):
    def __init__(self, ctx, musica_cog):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.musica_cog = musica_cog
        self.paused = False

    def disable_all_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.voice and interaction.user.voice.channel == self.ctx.voice_client.channel:
            vc = self.ctx.voice_client
            if not self.paused:
                vc.pause()
                self.paused = True
                button.label = "▶ Resume"
                await interaction.response.edit_message(view=self)
            else:
                vc.resume()
                self.paused = False
                button.label = "⏸ Pause"
                await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message(
                "You must be in the same voice channel to control playback.", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.danger)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.voice and interaction.user.voice.channel == self.ctx.voice_client.channel:
            vc = self.ctx.voice_client
            if vc.is_playing():
                vc.stop()
            await interaction.response.defer()
        else:
            await interaction.response.send_message(
                "You must be in the same voice channel to control playback.", ephemeral=True)
