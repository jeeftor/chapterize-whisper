from dataclasses import dataclass
from typing import List

@dataclass
class BookChapter:
    id: int
    start: float
    end: float
    title: str


def is_chapter(text: str) -> bool:
    # Convert text to lowercase and strip whitespace
    text = text.lower().strip()

    # Common chapter indicators
    chapter_patterns = {
        "chapter",
        "part ",
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


def parse_timestamp_srt(timestamp):
    # Split hours, minutes, seconds and milliseconds
    hours, minutes, seconds_ms = timestamp.split(':')
    seconds, milliseconds = seconds_ms.split(',')

    # Convert everything to integers
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    # Calculate total seconds
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000

    return total_seconds


def parse_chapter_file(chapter_file: str) -> List[BookChapter]:
    chapters: List[BookChapter] = []

    with open(chapter_file, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip()]

    for i, line in enumerate(lines[:-1]):  # Exclude the BOOK_END line
        timestamp, milliseconds, title = line.split(',', 2)  # Split only first two commas
        full_timestamp = f"{timestamp},{milliseconds}"

        start_time = parse_timestamp_srt(full_timestamp)

        # Get next line's timestamp for end time
        next_timestamp, next_ms, _ = lines[i + 1].split(',', 2)
        next_full_timestamp = f"{next_timestamp},{next_ms}"
        end_time = parse_timestamp_srt(next_full_timestamp)

        chapters.append(BookChapter(
            id=i + 1,
            start=start_time,
            end=end_time,
            title=title.strip()  # Remove any leading/trailing whitespace from title
        ))

    return chapters