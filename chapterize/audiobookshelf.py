import os
from dataclasses import dataclass
from glob import glob

import requests

from chapterize.utils import parse_chapter_file


# Chapter work https://api.audiobookshelf.org/#update-a-library-item-39-s-chapters



class ABSUpdater:

    def __init__(self, book_directory:str, abs_url: str, api_key: str) -> None:
        self.abs_url = abs_url
        self.api_key = api_key
        self.book_directory = book_directory
        self.chapters = parse_chapter_file(self._get_chapter_file())

    def _get_chapter_file(self):
        chapter_files = []
        chapter_files.extend(glob(os.path.join(self.book_directory, "*.chapters"), recursive=True))
        return chapter_files[0]


    def update_chapters(self, id: str):

        update_url = f"{self.abs_url}/api/items/{id}/chapters"

        # Convert chapters to the expected JSON format
        chapters_data = {
            "chapters": [
                {
                    "id": chapter.id,
                    "start": chapter.start,
                    "end": chapter.end,
                    "title": chapter.title
                }
                for chapter in self.chapters
            ]
        }
        # Set up headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make the POST request
        response = requests.post(
            update_url,
            headers=headers,
            json=chapters_data
        )

        # You might want to handle the response
        response.raise_for_status()  # Raises an exception for error status codes
        return response.json()  # Return the response data if needed








