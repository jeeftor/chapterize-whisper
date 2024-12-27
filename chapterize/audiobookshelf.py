import os
import sys
from dataclasses import dataclass
from glob import glob
from rich.prompt import Confirm
import requests
from urllib.parse import quote_plus

from chapterize.utils import parse_chapter_file
from rich.prompt import Prompt
from rich.console import Console

# Chapter work https://api.audiobookshelf.org/#update-a-library-item-39-s-chapters

from .const import  console

class ABSUpdater:

    def __init__(self, book_directory:str, abs_url: str, api_key: str) -> None:
        self.abs_url = abs_url
        self.api_key = api_key
        self.book_directory = book_directory
        self.chapters = parse_chapter_file(self._get_chapter_file())
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.libraries = self._get_libraries()


    def _get_chapter_file(self):
        chapter_files = []
        chapter_files.extend(glob(os.path.join(self.book_directory, "*.chapters"), recursive=True))
        return chapter_files[0]

    def _get_libraries(self) -> list[str]:
        """ Return a list of library IDs"""
        query_url = f"{self.abs_url}/api/libraries"

        try:
            response = requests.get(query_url,headers=self.headers)
        except requests.exceptions.RequestException as e:
            print(f"\nError querying libraries:")
            print(f"Status code: {getattr(e.response, 'status_code', 'N/A')}")
            print(f"Error message: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Server response: {error_detail}")
                except ValueError:
                    print(f"Raw server response: {e.response.text}")
            raise

        libs =response.json()['libraries']
        return [x['id'] for x in libs]

    def search(self) -> str|None:
        """ Search for books in all the libs."""
        basename=(os.path.basename(self.book_directory))
        query = quote_plus(basename)

        console.print(f"Searching libs for [green]{query}[/green]")
        search_results = {}

        for lib in self.libraries:
            console.print(f"Scanning library [yellow]{lib}[/yellow]")

            query_url = f"{self.abs_url}/api/libraries/{lib}/search?q={query}"
            try:
                response = requests.get(query_url, headers=self.headers)
            except requests.exceptions.RequestException as e:
                print(f"\nError querying libraries:")
                print(f"Status code: {getattr(e.response, 'status_code', 'N/A')}")
                print(f"Error message: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        print(f"Server response: {error_detail}")
                    except ValueError:
                        print(f"Raw server response: {e.response.text}")
                raise
            result = response.json()

            for book in result['book']:
                item = book['libraryItem']
                id = item['id']
                metadata = item['media']['metadata']
                title = metadata['title']
                author = metadata['authorName']
                search_results[f"{title} by {author}"] = id

        # If we found no books
        if len(search_results.keys()) == 0:
            console.print("[red]No books were found - did you upload the book yet?[/red]")
            return None
        elif len(search_results.keys()) == 1:
            key = list(search_results.keys())[0]
            book_id = search_results[key]
            console.print(f"Single book was found\n  [blue]Title:[/blue] [green]{key}[/green]\n  [blue]ID:[/blue] {book_id}")

            upload = Confirm.ask("Do you wish to update the chapters for this book")
            if not upload:
                sys.exit(0)
            return book_id
        else:
            # Prompt for which book
            # Convert dictionary keys to a list for indexing
            book_list = list(search_results.keys())

            # Display the numbered list
            for i, book in enumerate(book_list, 1):
                console.print(f"{i}. {book}")

            choice = Prompt.ask(
                "Which book would you like to select?",
                choices=[str(i) for i in range(1, len(book_list) + 1)]
            )

            # Get the selected book from the list of keys
            selected_book = book_list[int(choice) - 1]
            console.print(f"\nYou selected: [bold green]{selected_book}[/bold green]")

            # If you need the value associated with the selected book
            selected_book_value = search_results[selected_book]

            upload = Confirm.ask("Do you wish to update the chapters for this book")
            if not upload:
                sys.exit(0)
        return  selected_book_value
        pass

    def update_chapters(self, book_id: str):
        update_url = f"{self.abs_url}/api/items/{book_id}/chapters"

        print(f"\nProcessing chapters update for item ID: {book_id}")
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








