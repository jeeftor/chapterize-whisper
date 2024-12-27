import asyncio
import json
import os
from dotenv import load_dotenv

from chapterize.audiobookshelf import ABSUpdater
from chapterize.transcribe import BookTranscriber
from chapterize.utils import process_mps_results

# Load environment variables from .env file
load_dotenv()

async def mps_transcribe():
    # Setup a transcriber
    bt = BookTranscriber(os.getenv("INPUT_DIRECTORY"), use_mps=True)

    # Transcribe the file(s) please
    await bt.transcribe()

    #
    # with open("output.json", "r", encoding="utf8") as fp:
    #     results = json.load(fp)
    #
    # done_results = process_mps_results(results)
    #
    # with open("done.json", "w", encoding="utf8") as fp:
    #     json.dump(done_results, fp, ensure_ascii=False)


async def transcribe():

    # Setup a transcriber
    bt = BookTranscriber(os.getenv("INPUT_DIRECTORY"), use_mps=False)

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
    await mps_transcribe()
    # await update_chapters()

if __name__ == "__main__":
    asyncio.run(main())