class TMDBMatch:
    def __init__(self, data: dict):
        self.title = data.get("title")
        self.year = data.get("release_date")[:4]
        self.overview = data.get("overview")
        self.popularity = data.get("popularity")

    def __repr__(self):
        return f"""Title: {self.title}
        Release year: {self.year}
        Overview: {self.overview}
        Popularity Score: {self.popularity}"""


