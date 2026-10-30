from guessit import guessit

class Media():
    def __init__(path):
        guess = guessit(path)
        self.title = guess["title"]
        self.year = guess["year"]
        self.container = guess["container"]
        self.type = guess["type"]
