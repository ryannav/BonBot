from discord.ext import commands
import discord
import random
import config
import asyncio
from .currency import check_chips, user_found, adjust_chips

def determine_winner(player1, choice1, player2, choice2):
    if choice1 == choice2:
        msg = "It's a tie!"
    elif (choice1 == 'rock' and choice2 == 'scissors') or \
        (choice1 == 'paper' and choice2 == 'rock') or \
        (choice1 == 'scissors' and choice2 == 'paper'):
        msg = f"The winner of this game is {player1.mention} :trophy:"
        if config.wager > 0:
            adjust_chips('users.json', str(player1), config.wager)
            adjust_chips('users.json', str(player2), -config.wager)
            msg += f" You have won {config.wager} chips"
    else:
        msg = f"The winner of this game is {player2.mention} :trophy:"
        if config.wager > 0:
            adjust_chips('users.json', str(player2), config.wager)
            adjust_chips('users.json', str(player1), -config.wager)
            msg += f" You have won {config.wager} chips"
    return msg

def get_card_value(card):
    if card in ['J', 'Q', 'K']:
        return 10
    elif card == 'A':
        return 11 
    else:
        return int(card)
    
def calculate_hand_value(hand):
    return sum(hand['values'])


async def dealer_play(dealer_hand):
    while True:
        current_value = calculate_hand_value(dealer_hand)
        
        if current_value >= 17 and current_value <= 21:
            break
        
        if current_value > 21:
            if 11 in dealer_hand['values']:
                ace_index = dealer_hand['values'].index(11)
                dealer_hand['values'][ace_index] = 1
                current_value = calculate_hand_value(dealer_hand)
            else:
                break

        if current_value < 17:
            new_card = random.choice(config.deck)
            new_value = get_card_value(new_card)
            dealer_hand['cards'].append(new_card)
            dealer_hand['values'].append(new_value)
            current_value = calculate_hand_value(dealer_hand)
        

async def check_winner(ctx, amount, username):

    player_value = calculate_hand_value(config.hands['player'])
    dealer_value = calculate_hand_value(config.hands['dealer'])

    usrmessage = f"Player's hand: {config.hands['player']['cards']} with a total value of {player_value}.\nDealer's hand: {config.hands['dealer']['cards']} with a total value of {dealer_value}.\n"
    
    if player_value > 21 and dealer_value > 21:
        usrmessage += "Both busted, it's a tie."
    elif player_value > 21:
        usrmessage += "Player busts! Dealer wins."
        if amount != 0:
            adjust_chips('users.json', username, -amount)
            newchips = check_chips('users.json', username)
            usrmessage += f"\nYour chips were adjusted by {-amount}. you now have {newchips}"
    elif dealer_value > 21:
        usrmessage += "Dealer busts! Player wins."
        if amount != 0:
            adjust_chips('users.json', username, amount)
            newchips = check_chips('users.json', username)
            usrmessage += f"\nYour chips were adjusted by {amount}. you now have {newchips}"
    elif player_value > dealer_value:
        usrmessage += "Player wins!"
        if amount != 0:
            adjust_chips('users.json', username, amount)
            newchips = check_chips('users.json', username)
            usrmessage += f"\nYour chips were adjusted by {amount}. you now have {newchips}"
    elif dealer_value > player_value:
        usrmessage += "Dealer wins!"
        if amount != 0:
            adjust_chips('users.json', username, -amount)
            newchips = check_chips('users.json', username)
            usrmessage += f"\nYour chips were adjusted by {-amount}, you now have {newchips}"
    else:
        usrmessage += "It's a tie!"

    # Send the final message
    await ctx.send(usrmessage)

    # Clear hands after the round
    config.hands.clear()
    config.bjongoing_game = False

class Games(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name='joinRPS')
    async def join(self, ctx):
        
        if ctx.message.channel.type == discord.ChannelType.private:
            await ctx.send("Send this in a public channel")
            return
        
        if ctx.message.channel != config.game_channel:
            await ctx.send("Ongoing game in another channel")
            return
        
        for discord.Member in config.joined_users:
                if ctx.author.name == discord.Member.name:
                    await ctx.send(f"Bro, you were the one who started the game, you can't play with yourself")
                    return
        username = ctx.author.name
        chips_value = check_chips('users.json', username)
        if(config.wager > 0 and user_found == False):
            await ctx.send("Get your initial aura first by using =aura. Then get some chips using =daily")
            return
        if(config.wager > 0 and config.wager > chips_value):
            await ctx.send("insufficient funds, =chips to check your balance")
            return
        
        if config.join_allowed:
            config.game_channel = ctx.message.channel
            config.joined_users.add(ctx.author)
            joined_names = ", ".join(discord.Member.name for discord.Member in config.joined_users)
            await ctx.send(f"This match will include {joined_names}")
            config.join_event.set()
            config.join_allowed = False
            await ctx.author.send("Please choose Rock, Paper, or Scissors.")
            config.game_event = asyncio.Event()
            try:
                await asyncio.wait_for(config.game_event.wait(), timeout=config.join_time_limit)
            except asyncio.TimeoutError:
                await ctx.send("Time's up! the responses were not given in time")
                config.game_in_progress = False
                config.join_allowed = False
                config.joined_users.clear()
                config.wager = 0
                config.game_channel=0
                return
        else:
            await ctx.send("Joining is currently not allowed. Please wait for the next playRPS command.")


    @commands.command(name='playRPS')
    async def play(self, ctx, amount:int = 0):

        if ctx.message.channel.type == discord.ChannelType.private:
            await ctx.send("Send this in a public channel")
            return
        
        if config.game_in_progress:
            await ctx.send("A game is already in progress. Please wait for it to finish.")
            return
        username = ctx.author.name
        chips_value = check_chips('users.json', username)
        if(amount > 0 and user_found == False):
            await ctx.send("Get your initial aura first by using =aura. Then get some chips using =daily")
            return
        if(amount > 0 and amount > chips_value):
            await ctx.send("insufficient funds, =chips to check your balance")
            return
        if(amount < 0 ):
            await ctx.send("cannot bet negative value")
            return
        
        config.game_in_progress = True
        config.joined_users.add(ctx.author)
        config.join_allowed = True
        config.join_event = asyncio.Event()
        await ctx.send("You have 30 seconds to join by using the =joinRPS command!")
        config.game_channel = ctx.message.channel
        config.wager = amount

        try:
            await asyncio.wait_for(config.join_event.wait(), timeout=config.join_time_limit)
        except asyncio.TimeoutError:
            await ctx.send("Time's up! Nobody joined the game.")
            config.game_in_progress = False
            config.join_allowed = False
            config.joined_users.clear()
            config.wager = 0
            config.game_channel = 0
            return

        await ctx.send("Joining period is over!")
        config.join_allowed = False
        await ctx.author.send("Please choose Rock, Paper, or Scissors.")


        config.join_allowed = False
                    
        

    #BlackJack Game, want to eventually add ability to gamble and multiplayer mode
    #the dealer works autonimously
    #the user chooses the hit or stand and Aces automatically change if

    async def player_play(self, ctx, player_hand):
        while True:
            current_value = calculate_hand_value(player_hand)
            
            if current_value >= 21:
                break

            await ctx.send("Hit or Stand? Type 'hit' or 'stand'.")

            def check(msg):
                return msg.author == ctx.author and msg.content.lower() in ['hit', 'stand']
            
            try:
                msg = await asyncio.wait_for(self.client.wait_for('message', check=check), timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Timeout reached. Ending game.")
                config.bjongoing_game = False
                config.hands.clear()
                return

            if msg.content.lower() == 'hit':
                new_card = random.choice(config.deck)
                new_value = get_card_value(new_card)
                player_hand['cards'].append(new_card)
                player_hand['values'].append(new_value)
                current_value = calculate_hand_value(player_hand)
                await ctx.send(f"You draw {new_card} (total: {current_value}).")
                
                while current_value > 21 and 11 in player_hand['values']:
                    ace_index = player_hand['values'].index(11)
                    player_hand['values'][ace_index] = 1
                    current_value = calculate_hand_value(player_hand)
                    await ctx.send(f"Adjusted ace value. New total: {current_value}")

                if current_value > 21:
                    await ctx.send("You bust!")
                    return
            else:
                break


    @commands.command(name='bj')
    async def bj(self, ctx, amount: int = 0):
        if config.bjongoing_game:
            await ctx.send("Ongoing game, wait for it to finish")
            return
        username = ctx.author.name
        chips_value = check_chips('users.json', username)
        if(amount > 0 and user_found == False):
            await ctx.send("Get your initial aura first by using =aura. Then get some chips using =daily")
            return
        if(amount > 0 and amount > chips_value):
            await ctx.send("insufficient funds, =chips to check your balance")
            return
        if(amount < 0 ):
            await ctx.send("cannot bet negative value")
            return
        
        await ctx.send("BlackJack has been started, dealing cards...")
        config.bjongoing_game = True

        c1 = random.choice(config.deck)
        c2 = random.choice(config.deck)
        d1 = random.choice(config.deck)
        d2 = random.choice(config.deck)

        c1_value = get_card_value(c1)
        c2_value = get_card_value(c2)
        d1_value = get_card_value(d1)
        d2_value = get_card_value(d2)

        config.hands['player'] = {'cards': [c1, c2], 'values': [c1_value, c2_value]}
        config.hands['dealer'] = {'cards': [d1, d2], 'values': [d1_value, d2_value]}

        if 'A' in config.hands['player']['cards']:
            await ctx.send(f"Your current cards are {config.hands['player']['cards']}. Do you want your ace to be worth 1 or 11?")

            def check(msg):
                return msg.author == ctx.author and msg.content in ['1', '11']
            try:
                msg = await asyncio.wait_for(self.client.wait_for('message', check=check), timeout=30.0)
            except asyncio.TimeoutError:
                await ctx.send("Timeout reached. Ending game.")
                config.bjongoing_game = False
                config.hands.clear()
                return
            
            ace_value = int(msg.content)
            ace_index = config.hands['player']['cards'].index('A')
            config.hands['player']['values'][ace_index] = ace_value

        await ctx.send(f"Your current cards are {config.hands['player']['cards']} with a total value of {calculate_hand_value(config.hands['player'])}. The dealer has {d1} and *hidden*")

        await self.player_play(ctx, config.hands['player'])
        if not config.hands:
            return
        await dealer_play(config.hands['dealer'])
        await check_winner(ctx, amount, username)


    @commands.command(name='slots')
    async def slots(self, ctx, amount: int=0):
        username = ctx.author.name
        chips_value = check_chips('users.json', username)
        if(amount > 0 and user_found == False):
            await ctx.send("Get your initial aura first by using =aura. Then get some chips using =daily")
            return
        if(amount > 0 and amount > chips_value):
            await ctx.send("insufficient funds, =chips to check your balance")
            return
        if(amount < 0 ):
            await ctx.send("cannot bet negative value")
            return
        result = [[random.choice(config.symbols) for _ in range(3)] for _ in range(3)]
        result_str = '\n'.join([' '.join(row) for row in result])

        await ctx.send(f'you spun:\n{result_str}')

        # Check if the user won
        win_amount = self.check_payout(result, amount)
        if win_amount > 0:
            adjust_chips('users.json' ,username, win_amount)
            await ctx.send(f'{ctx.author.mention}, you won {win_amount} chips! 🎉')
        else:
            adjust_chips('users.json' ,username, -amount)
            await ctx.send(f'{ctx.author.mention}, you lost {amount} chips. Better luck next time!')
    
    
    def check_payout(self, result, bet):
        """ Check rows, columns, and diagonals for winning combinations """
        lines = []
        # Add rows
        lines.extend(result)
        # Add columns
        lines.extend([[result[r][c] for r in range(3)] for c in range(3)])
        # Add diagonals
        lines.append([result[i][i] for i in range(3)])
        lines.append([result[i][2-i] for i in range(3)])

        for line in lines:
            if len(set(line)) == 1:  # All symbols in the line are the same
                symbol_combination = ''.join(line)
                if symbol_combination in config.payouts:
                    return config.payouts[symbol_combination] * bet
        return 0

async def setup(client):
    await client.add_cog(Games(client))