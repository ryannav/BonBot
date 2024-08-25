joined_users = set()  # Set to keep track of users who have joined
join_allowed = False  # Flag to allow joining
join_time_limit = 30  # Time limit for joining in seconds
join_event = None
game_in_progress = False
game_channel = 0
wager = 0
deck = [2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,6,6,7,7,7,7,8,8,8,8,9,9,9,9,10,10,10,10,'J','J','J','J','Q','Q','Q','Q','K','K','K','K','A','A','A','A']
bjongoing_game = False
hands = {}
last_daily_usage = {}
sent_messages = {}
gamble_usage = {}
choices = {}
symbols = [":seven:", ":cherries:", ":star:", ":grapes:", ":bell:", ":tangerine:", ":lemon:", ":eggplant:"]

payouts = {
    ":cherries::cherries::cherries:": 5,
    ":lemon::lemon::lemon:": 6,
    ":eggplant::eggplant::eggplant:": 7,
    ":tangerine::tangerine::tangerine:": 8,
    ":grapes::grapes::grapes:": 9,
    ":bell::bell::bell:": 10,
    ":star::star::star:": 13,
    ":seven::seven::seven:": 15
}