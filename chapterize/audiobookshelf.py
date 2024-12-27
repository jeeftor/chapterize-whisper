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

        print(f"\nProcessing chapters update for item ID: {id}")
        print(f"Total chapters to update: {len(self.chapters)}")

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

        # Print chapter details before sending
        print("\nChapter details to be updated:")
        for idx, chapter in enumerate(self.chapters, 1):
            print(f"  Chapter {idx:02d}: '{chapter.title}' ({chapter.start} - {chapter.end})")

        # Set up headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        print(f"\nSending update request to: {update_url}")

        # Make the POST request
        try:
            response = requests.post(
                update_url,
                headers=headers,
                json=chapters_data
            )

            # Handle the response
            response.raise_for_status()
            response_data = response.json()

            print(f"\nUpdate successful!")
            print(f"Response status code: {response.status_code}")
            print(f"Updated chapters count: {len(response_data.get('chapters', []))}")

            return response_data

        except requests.exceptions.RequestException as e:
            print(f"\nError updating chapters:")
            print(f"Status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Server response: {error_detail}")
                except ValueError:
                    print(f"Raw server response: {e.response.text}")
            raise








