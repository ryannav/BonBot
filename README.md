# BonBonBot
This is the repository to work on the functionality for BonBonBot

requires .env file that includes
DISCORD_TOKEN = [DISCORD TOKEN]
api_key = [API KEY]
DB_HOST=[ADDRESS WHERE DATABASE IS HOSTED]
DB_USER=[USERNAME FOR OWNER OF DATABASE]
DB_PASSWORD=[PASSWORD FOR DATABASE]
DB_NAME=[NAME OF DATABASE]

if you are on windows set ffmeg_path = os.path.join(BASE_DIR, "bin", "ffmpeg", "ffmpeg.exe") in musica.py at the moment it is preset for linux

To set up vscode environment put the following in the terminal, 
1. python -m venv venv
2. venv\Scripts\activate
3. pip install discord
4. pip install requests
5. pip install python-dotenv
6. pip install discord yt_dlp (if on Windows)
7. sudo apt install ffmeg (if on Linux)
8. pip install mysql-connector-python
9. create a .env file in your folder and add the text DISCORD_TOKEN = '*your_token*'

To run type: python main.py
