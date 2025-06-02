import os
import mysql.connector
from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

class Playlists(commands.Cog):
    def __init__(self, client):
        self.client = client

    def _get_db_connection(self):
        return mysql.connector.connect(**DB_CONFIG)

    @commands.command(name="playlisthelp")
    async def helpme(self, ctx):
        """Show a list of available playlist commands."""
        help_text = (
            "**Playlist Commands:**\n"
            "`=createplaylist <name> [public/private]` - Create a new playlist e.g. !createplaylist \"BonBon Playlist\" public.\n"
            "`=addsong <playlist_name> <song>` - Add a song (title or URL) to a playlist.\n"
            "`=showpublic` - List all public playlists and their owners.\n"
            "`=myplaylists` - List your own playlists.\n"
            "`=playlist <playlist_name>` - Play all songs in a playlist.\n"
            "`=showplaylist <playlist_name>` - View all songs in a playlist.\n"
        )
        await ctx.send(help_text)

    @commands.command()
    async def createplaylist(self, ctx, playlist_name: str, visibility: str = "private"):
        """Create a new playlist. Usage: !createplaylist <name> [public/private]"""
        user_name = str(ctx.author.name)
        is_public = 1 if visibility.lower() == "public" else 0

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Check if playlist with this name already exists for this user
        cursor.execute("SELECT id FROM playlists WHERE name = %s AND owner = %s", (playlist_name, user_name))
        if cursor.fetchone():
            await ctx.send(f"⚠️ You already have a playlist named `{playlist_name}`.")
            cursor.close()
            conn.close()
            return

        # Insert new playlist
        cursor.execute(
            "INSERT INTO playlists (name, owner, is_public) VALUES (%s, %s, %s)",
            (playlist_name, user_name, is_public)
        )
        conn.commit()
        cursor.close()
        conn.close()

        await ctx.send(f"✅ Playlist `{playlist_name}` created as {'public' if is_public else 'private'}.")

    @commands.command(aliases=['addsong'])
    async def add_song(self, ctx, playlist_name: str, *, song: str):
        """Add a song title or URL to a playlist. Usage: !addsong <playlist_name> <song>"""
        user_name = str(ctx.author.name)

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get playlist info
        cursor.execute("SELECT id, owner, is_public FROM playlists WHERE name = %s", (playlist_name,))
        playlist = cursor.fetchone()

        if not playlist:
            await ctx.send(f"❌ Playlist `{playlist_name}` does not exist.")
            cursor.close()
            conn.close()
            return

        playlist_id, owner, is_public = playlist

        # Permission check: if private and not owner, reject
        if is_public == 0 and owner != user_name:
            await ctx.send(f"❌ You don’t own the private playlist `{playlist_name}`.")
            cursor.close()
            conn.close()
            return

        # Distinguish between URL and title (basic check)
        song_title = song
        song_url = song if song.startswith("http://") or song.startswith("https://") else None

        cursor.execute(
            """INSERT INTO playlist_songs 
            (playlist_id, song_title, song_url, user_name, is_public) 
            VALUES (%s, %s, %s, %s, %s)""",
            (playlist_id, song_title, song_url, user_name, is_public)
        )
        conn.commit()
        cursor.close()
        conn.close()

        await ctx.send(f"✅ Added to `{playlist_name}`: **{song_title}**")

    @commands.command()
    async def showpublic(self, ctx):
        """Show all public playlists and their owners."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, owner FROM playlists WHERE is_public = 1")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            await ctx.send("No public playlists found.")
            return

        embed = discord.Embed(title="Public Playlists", color=discord.Color.blue())
        for name, owner in results:
            embed.add_field(name=name, value=f"Owner: {owner}", inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def myplaylists(self, ctx):
        """Show your playlists."""
        user_name = str(ctx.author.name)
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, is_public FROM playlists WHERE owner = %s", (user_name,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            await ctx.send("You don’t have any playlists yet.")
            return

        embed = discord.Embed(title=f"{user_name}'s Playlists", color=discord.Color.green())
        for name, is_public in results:
            vis = "Public" if is_public else "Private"
            embed.add_field(name=name, value=vis, inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def playlist(self, ctx, playlist_name: str):
        """Play a playlist by name. Usage: !playlist <playlist_name>"""
        user_name = str(ctx.author.name)
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get playlist info
        cursor.execute("SELECT id, owner, is_public FROM playlists WHERE name = %s", (playlist_name,))
        playlist = cursor.fetchone()

        if not playlist:
            await ctx.send(f"❌ Playlist `{playlist_name}` not found.")
            cursor.close()
            conn.close()
            return

        playlist_id, owner, is_public = playlist

        # Permission check for private playlist
        if is_public == 0 and owner != user_name:
            await ctx.send("❌ You don't have permission to play this private playlist.")
            cursor.close()
            conn.close()
            return

        # Get songs in playlist
        cursor.execute(
            "SELECT song_title, song_url FROM playlist_songs WHERE playlist_id = %s ORDER BY added_at ASC",
            (playlist_id,)
        )
        songs = cursor.fetchall()
        cursor.close()
        conn.close()

        if not songs:
            await ctx.send(f"⚠️ Playlist `{playlist_name}` is empty.")
            return

        musica_cog = self.client.get_cog("Musica")
        if not musica_cog:
            await ctx.send("❌ Musica module not loaded.")
            return

        # Play all songs (pass URL if available, else title)
        for song_title, song_url in songs:
            search_query = song_url if song_url else song_title
            await musica_cog.play(ctx, search=search_query)

        embed = discord.Embed(
            title="📀 Playlist Queued",
            description=f"Playlist '{playlist_name}' has been queued!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def showplaylist(self, ctx, playlist_name: str):
        """View all songs in a playlist. Usage: !showplaylist <playlist_name>"""
        user_name = str(ctx.author.name)
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Fetch playlist info
        cursor.execute("SELECT id, owner, is_public FROM playlists WHERE name = %s", (playlist_name,))
        playlist = cursor.fetchone()

        if not playlist:
            await ctx.send(f"❌ Playlist `{playlist_name}` not found.")
            cursor.close()
            conn.close()
            return

        playlist_id, owner, is_public = playlist

        # Permission check
        if is_public == 0 and owner != user_name:
            await ctx.send("❌ You don't have permission to view this private playlist.")
            cursor.close()
            conn.close()
            return

        # Get songs
        cursor.execute(
            "SELECT song_title, song_url FROM playlist_songs WHERE playlist_id = %s ORDER BY added_at ASC",
            (playlist_id,)
        )
        songs = cursor.fetchall()
        cursor.close()
        conn.close()

        if not songs:
            await ctx.send(f"⚠️ Playlist `{playlist_name}` is empty.")
            return

        embed = discord.Embed(
            title=f"🎶 Playlist: {playlist_name}",
            description=f"Created by: {owner} | Visibility: {'Public' if is_public else 'Private'}",
            color=discord.Color.purple()
        )

        for i, (title, url) in enumerate(songs[:25], start=1):
            if url:
                song_display = f"{i}. [{title}]({url})"
            else:
                song_display = f"{i}. {title}"
            embed.add_field(name="\u200b", value=song_display, inline=False)

        if len(songs) > 25:
            embed.set_footer(text=f"And {len(songs) - 25} more...")

        await ctx.send(embed=embed)

    @commands.command()
    async def deletesong(self, ctx, playlist_name: str, *, song_title: str):
        """Delete a song from a playlist. Only the playlist owner can delete songs."""
        user_name = str(ctx.author.name)
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get playlist info
        cursor.execute("SELECT id, owner FROM playlists WHERE name = %s", (playlist_name,))
        playlist = cursor.fetchone()
        if not playlist:
            await ctx.send(f"❌ Playlist `{playlist_name}` does not exist.")
            return

        playlist_id, owner = playlist

        if owner != user_name:
            await ctx.send("❌ You don’t have permission to delete songs from this playlist.")
            return

        # Attempt to delete
        cursor.execute(
            "DELETE FROM playlist_songs WHERE playlist_id = %s AND song_title = %s",
            (playlist_id, song_title)
        )
        conn.commit()
        rows_deleted = cursor.rowcount
        cursor.close()
        conn.close()

        if rows_deleted == 0:
            await ctx.send(f"⚠️ Song `{song_title}` not found in playlist `{playlist_name}`.")
        else:
            await ctx.send(f"🗑️ Removed `{song_title}` from `{playlist_name}`.")

    @commands.command()
    async def deleteplaylist(self, ctx, *, playlist_name: str):
        """Delete your playlist. Confirmation required."""
        user_name = str(ctx.author.name)
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Check ownership
        cursor.execute("SELECT id FROM playlists WHERE name = %s AND owner = %s", (playlist_name, user_name))
        playlist = cursor.fetchone()
        if not playlist:
            await ctx.send(f"❌ Playlist `{playlist_name}` not found or you don't own it.")
            cursor.close()
            conn.close()
            return

        playlist_id = playlist[0]
        cursor.close()
        conn.close()

        # Ask for confirmation
        await ctx.send(f"⚠️ Are you sure you want to delete the playlist `{playlist_name}`? Reply with `yes` to confirm.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'yes'

        try:
            confirmation = await self.client.wait_for('message', check=check, timeout=20.0)
        except asyncio.TimeoutError:
            await ctx.send("⏳ Playlist deletion canceled.")
            return

        # Proceed with deletion
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = %s", (playlist_id,))
        cursor.execute("DELETE FROM playlists WHERE id = %s", (playlist_id,))
        conn.commit()
        cursor.close()
        conn.close()

        await ctx.send(f"✅ Playlist `{playlist_name}` has been deleted.")


async def setup(client):
    await client.add_cog(Playlists(client))
