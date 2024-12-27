import asyncio
import os
from dotenv import load_dotenv

from chapterize.audiobookshelf import ABSUpdater
from chapterize.transcribe import BookTranscriber

# Load environment variables from .env file
load_dotenv()

async def transcribe():

    # Setup a transcriber
    bt = BookTranscriber(os.getenv("INPUT_DIRECTORY"))

    # Transcribe the file(s) please
    await bt.transcribe()


    # Your async code here
    print("Running async main function")
    await asyncio.sleep(1)
    print("Finished async main function")


async def update_chapters():
    updater = ABSUpdater(os.getenv("BOOK_DIRECTORY"), os.getenv("ABS_URL"), os.getenv("ABS_API_KEY"))

    # updater.update_chapters(os.getenv("BOOK_ID"))

    updater.search()

async def main():

    # await transcribe()
    await update_chapters()

if __name__ == "__main__":
    asyncio.run(main())