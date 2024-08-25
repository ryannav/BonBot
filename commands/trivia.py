import discord
from discord.ext import commands
import requests
import json

class Trivia(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(name='abouttrivia')
    async def abouttrivia(self, ctx):
        embedVar = discord.Embed(title="Commands for Trivia game", description="How to play the game:", color=0x552583)
        embedVar.add_field(name="=trivia category difficulty question_type", value="Set the category, difficulty, and question type to one of the options below.\nPut a space between each section of the request.", inline=False)
        embedVar.add_field(name="Category", value="For a list of categories, do `=categories`", inline=False)
        embedVar.add_field(name="Difficulty", value="Put: Easy, Medium, or Hard", inline=False)
        embedVar.add_field(name="Question Type", value="Put: MC or TF (multiple choice or True/False)", inline=False)
        embedVar.add_field(name="Answering", value="For MC put 1, 2, 3... For TF put True or False", inline=False)
        await ctx.send(embed=embedVar)

    def get_trivia_question(self, category, difficulty, question_type):
        url = 'https://opentdb.com/api.php'
        params = {
            'amount': 1,
            'category': category,
            'difficulty': difficulty,
            'type': question_type
        }
        response = requests.get(url, params=params)
        data = response.json()
        if data['response_code'] == 0:
            return data['results'][0]
        else:
            return None

    def load_categories_from_file(self):
        with open('categories.json', 'r') as file:
            data = json.load(file)
        categories = {category['name'].lower(): category['id'] for category in data['trivia_categories']}
        return categories

    @commands.command(name='categories')
    async def list_categories(self, ctx):
        categories = self.load_categories_from_file()
        available_categories = "\n".join(categories.keys())
        await ctx.send(f"Available categories:\n{available_categories}")
    
    @commands.command(name='trivia')
    async def trivia(self, ctx, category: str, difficulty: str, question_type: str):
        try:
            category = category.lower()
            difficulty = difficulty.lower()
            question_type = question_type.lower()

            #need to check that difficulty and question type are correctly input
            if(difficulty == "easy" or difficulty == "medium" or difficulty == "hard"):
                if(question_type == "mc" or question_type == "tf"):
                    if(question_type == "mc"):
                        question_type = "multiple"
                    else:
                        question_type = "boolean"

                    categories = self.load_categories_from_file()
                    category = category.lower()
                    if category in categories:
                        category_id = categories[category]
                        question_data = self.get_trivia_question(category_id, difficulty, question_type)
                        if question_data:
                            question = question_data['question']
                            correct_answer = question_data['correct_answer']
                            incorrect_answers = question_data['incorrect_answers']

                            if question_type == 'multiple':
                                options = incorrect_answers + [correct_answer]
                                options.sort()

                                options_str = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
                                await ctx.send(f"{question}\n\n{options_str}")

                                def check_answer(m):
                                    return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= len(options)

                                answer_msg = await self.client.wait_for('message', check=check_answer)
                                answer_index = int(answer_msg.content) - 1
                                if options[answer_index] == correct_answer:
                                    await ctx.send("Correct!")
                                    #maybe add in functionality to give people aura points?
                                else:
                                    await ctx.send(f"Wrong! The correct answer was: {correct_answer}")
                                    #maybe add functionality to take aura points
                            elif question_type == 'boolean':
                                await ctx.send(f"{question}\n\nTrue or False?")

                                def check_answer(m):
                                    return m.author == ctx.author and m.content.lower() in ['true', 'false']

                                answer_msg = await self.client.wait_for('message', check=check_answer)
                                if answer_msg.content.lower() == correct_answer.lower():
                                    await ctx.send("Correct!")
                                    #maybe add in functionality to give people aura points?
                                else:
                                    await ctx.send(f"Wrong! The correct answer was: {correct_answer}")
                                    #maybe add functionality to take aura points
                        else:
                            await ctx.send("Could not retrieve trivia question. Please check the category, difficulty, and type.")
                    else:
                        await ctx.send(f"Category '{category}' not found. Please choose from the available categories.")
                else:
                    await ctx.send(f"The question type isnt set correctly. Please enter 'MC' or 'TF'")
            else:
                await ctx.send(f"The difficulty isnt set correctly. Please enter 'Easy', 'Medium', or 'Hard'")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

   

async def setup(client):
    await client.add_cog(Trivia(client))