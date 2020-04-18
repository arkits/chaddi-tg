# Encapsulate data representing a Bakchod
class Bakchod:
    def __init__(self, id, username, first_name):

        # Telegram ID
        self.id = id

        # Telegram Username
        self.username = username

        # Telegram Username
        self.first_name = first_name

        # Last seen on Telegram as a Date
        self.lastseen = None

        # Rokda. Initialized to 500
        self.rokda = 500

        # User's Birthday as a Date
        self.birthday = None

        # History Dictionary
        # key="history_type", value=Date
        self.history = {}

        # Modifiers Dictionary
        self.modifiers = {}

    @classmethod
    def fromUpdate(cls, update):

        id = update.message.from_user.id
        username = update.message.from_user.username
        first_name = update.message.from_user.first_name

        return cls(id, username, first_name)
