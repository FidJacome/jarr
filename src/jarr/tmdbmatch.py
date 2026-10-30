class TMDBMatch:
    def __init__(self, data: dict):
        self.id = data.get("id")
        self.title = data.get("title") or data.get("name")
        date = data.get("release_date") or data.get("first_air_date")
        self.year = date[:4] if date else None
        self.overview = data.get("overview")
        self.popularity = data.get("popularity")

    def __repr__(self):
        return f"Title: {self.title}\nRelease year: {self.year}\nOverview: {self.overview}\nPopularity Score: {self.popularity}"


