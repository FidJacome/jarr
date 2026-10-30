from guessit import guessit

class Media:
    def __init__(self, path, title, year, kind, extension, season=None, episode=None):
        self.path = path
        self.title = title
        self.year = year
        self.kind = kind
        self.extension = extension
        self.season = season
        self.episode = episode

    @classmethod
    def from_path(cls, path):
        guess = guessit(path)
        return cls(
            path=path,
            title=guess["title"],
            year=guess.get("year"),
            kind=guess.get("type"),
            extension=path.suffix,
            season=guess.get("season"),
            episode=guess.get("episode"),
        )
