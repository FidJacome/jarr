from guessit import guessit

def parse(file: str) -> str:
    content = guessit(file)
    return f"{content.get("title")} ({content.get("year")}).{content.get("container")}"
