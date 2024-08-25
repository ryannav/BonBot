from discord.ext import commands
import random
from datetime import datetime, timedelta
import json
import config


#used to change a users aura, amount is amount you want to change it by
def adjust_chips(file_path, username, amount):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    for user in data["users"]:
        if user["name"] == username:
            chips = user["chips"]
            change = amount
            new_chips = str(int(chips) + change)
            user["chips"] = new_chips 
            with open('users.json', 'w') as file:
                json.dump(data, file, indent=4)
            return

def check_chips(file_path, username):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    for user in data["users"]:
        if user["name"] == username:
            chips = user["chips"]
            return int(chips)

        

def user_found(file_path, username):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    # Check if the user already exists
    for user in data["users"]:
        if user["name"] == username:
            return True
    return False

def check_and_add_user(file_path, username):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    # Check if the user already exists
    for user in data["users"]:
        if user["name"] == username:
            return user["aura"]
    # If the user does not exist, add them with a random aura value
    new_aura = str(random.randint(-200, 900))
    new_user = {
        "name": username,
        "aura": new_aura,
        "chips": "0"
    }
    data["users"].append(new_user)
    # Save the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return new_aura

#used to change a users aura, amount is amount you want to change it by
def adjust_aura(file_path, username, amount):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    for user in data["users"]:
        if user["name"] == username:
            aura = user["aura"]
            change = amount
            new_aura = str(int(aura) + change)
            user["aura"] = new_aura 
            with open('users.json', 'w') as file:
                json.dump(data, file, indent=4)
            return

def check_aura(file_path, username):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {"users": []}
    for user in data["users"]:
        if user["name"] == username:
            aura = user["aura"]
            return int(aura)

class Currency(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command(name='aura')
    async def aura(self,ctx):
        username = ctx.author.name  # Get the username of the person who invoked the command
        aura_value = check_and_add_user('users.json', username)
        if int(aura_value) < 0 :
            await ctx.send(f'{ctx.author.mention}, your aura is {aura_value}. You are currently in aura debt')
            await ctx.send('https://tenor.com/view/laughing-cat-catlaughing-laughingcat-point-gif-7577620470218150413')
        else :
            await ctx.send(f'{ctx.author.mention}, your current aura is {aura_value}')

    @commands.command(name='ranking')
    async def ranking(self,ctx):
        try:
            with open('users.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            await ctx.send("No users found.")
            return
        
        # Sort users by aura value in descending order
        users = data["users"]
        sorted_users = sorted(users, key=lambda x: int(x["aura"]), reverse=True)
        
        # Create a formatted string with the sorted users
        if not sorted_users:
            await ctx.send("No users found.")
            return
        
        rankings_message = "Rankings:\n"
        for i, user in enumerate(sorted_users, start=1):
            rankings_message += f"{i}. {user['name']}: {user['aura']}\n"
        
        # Send the rankings message
        await ctx.send(f'```{rankings_message}```')

    @commands.command(name='chips')
    async def chips(self,ctx):
        username = ctx.author.name  # Get the username of the person who invoked the command
        if user_found('users.json', username) == True:
            chips_value = check_chips('users.json', username)
            await ctx.send(f'{ctx.author.mention}, you have {chips_value} chips.')
        else:
            await ctx.send(f'{ctx.author.mention}, get your initial aura by typing =aura first')

    @commands.command(name='ca')
    async def ca(self,ctx, conversion: int = None):
        username = ctx.author.name
        
        if conversion is None:
            await ctx.send("You must specify the amount of aura you want to convert ex.(=ca 100).")
            return
        
        if user_found('users.json', username) == True:
            numaura = check_aura('users.json', username)
            if numaura < conversion or conversion < 0:
                await ctx.send(f'{ctx.author.mention}, Invalid amount, `=aura` to check your current aura')
            else:
                adjust_aura('users.json', username, -conversion)
                adjust_chips('users.json', username, conversion*10)
                currchips = check_chips('users.json', username)
                await ctx.send(f'{ctx.author.mention}, you have added {conversion*10} chips to your collection. You now have {currchips} chips.')
        else:
            await ctx.send(f'{ctx.author.mention}, get your initial aura by typing =aura first')

    @commands.command(name='cc')
    async def cc(self,ctx, conversion: int = None):
        if conversion is None:
            await ctx.send("You must specify the amount of chips you want to convert ex.(=cc 100).")
            return
        username = ctx.author.name
        if user_found('users.json', username) == True:
            numchips = check_chips('users.json', username)
            if conversion % 10 != 0 or conversion < 0:
                await ctx.send(f'{ctx.author.mention}, Invalid amount. Conversion amount must be a positive number divisible by 10. Use `=chips` to check your current number of chips.')
            elif numchips < conversion:
                await ctx.send(f'{ctx.author.mention}, Insufficient chips. Use `=chips` to check your current chips.')
            else:
                adjust_chips('users.json', username, -conversion)
                adjust_aura('users.json', username, int(conversion/10))
                newtotal = check_aura('users.json', username)
                await ctx.send(f'{ctx.author.mention}, you have added {conversion/10} aura to your total. You now have {newtotal} aura.')
        else:
            await ctx.send(f'{ctx.author.mention}, get your initial aura by typing =aura first')


    @commands.command(name='daily')
    async def daily(self,ctx):
        username = ctx.author.name  # Get the username of the person who invoked the command
        
        # Check if the user has used the command recently
        if username in config.last_daily_usage:
            last_used = config.last_daily_usage[username]
            cooldown_time = timedelta(days=1)  # 1 day cooldown

            if datetime.now() - last_used < cooldown_time:
                remaining_time = cooldown_time - (datetime.now() - last_used)
                await ctx.send(f"{ctx.author.mention}, you can only claim your daily once per day. Please wait {remaining_time} before claiming it again.")
                return
            
        if user_found('users.json', username):
            adjust_chips('users.json', username, 500)
            numchips = check_chips('users.json', username)
            config.last_daily_usage[username] = datetime.now()
            await ctx.send(f'500 chips have been added, you now have {numchips} chips.')
        else:
            await ctx.send(f'{ctx.author.mention}, get your initial aura by typing =aura first')

    @commands.command(name='gambleaura')
    async def gambleaura(self,ctx):
        username = ctx.author.name  # Get the username of the person who invoked the command
        current_time = datetime.now()

        # Check if the user has used the command before
        if username in config.gamble_usage:
            last_used, usage_count = config.gamble_usage[username]
            time_difference = current_time - last_used

            # Check if the last usage was within the last hour
            if time_difference < timedelta(hours=1):
                if usage_count >= 3:
                    await ctx.send(f'{ctx.author.mention}, you can only use the =gambleaura command 3 times per hour. Please try again later.')
                    return
                else:
                    config.gamble_usage[username] = (current_time, usage_count + 1)
            else:
                config.gamble_usage[username] = (current_time, 1)
        else:
            config.gamble_usage[username] = (current_time, 1)

        try:
            with open('users.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {"users": []}
        
        # Check if the user already exists
        for user in data["users"]:
            if user["name"] == username:
                aura = user["aura"]
                rand = random.randint(-600, 600)
                new_aura = str(int(aura) + rand)
                user["aura"] = new_aura 
                with open('users.json', 'w') as file:
                    json.dump(data, file, indent=4)
                await ctx.send(f'{ctx.author.mention}, your current aura is {new_aura}. It has changed by {rand}')
                return
        
        # If the user does not exist, add them with a random aura value
        await ctx.send(f'You have not gotten your initial aura reading, use the "=aura" command to get it.')

async def setup(client):
    await client.add_cog(Currency(client))