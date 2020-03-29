# Encapsulate data representing a Group
class Group:
    def __init__(self, id, title):

        # Telegram ID
        self.id = id

        # Group Title
        self.title = title

        # List of group member IDs
        self.members = []

    @classmethod
    def fromUpdate(cls, update):

        id = update.message.chat.id
        title = update.message.chat.title

        return cls(id, title)
