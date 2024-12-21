def is_chapter(text: str) -> bool:
    # Convert text to lowercase and strip whitespace
    text = text.lower().strip()

    # Common chapter indicators
    chapter_patterns = {
        "chapter",
        "part",
        "book",
        "section",
        "prologue",
        "prolog",
        "epilogue",
        "epilog",
        "introduction",
        "interlude",
        "intermission",
        "afterword",
        "foreword",
        "preface",
        "appendix"
    }

    roman_numerals = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}

    return any((
        text.startswith(pattern) for pattern in chapter_patterns
                                                or text.isdigit()
                                                or text in roman_numerals
    ))

def format_timestamp_srt(seconds: float, offset: float) -> str:
    seconds += offset
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"