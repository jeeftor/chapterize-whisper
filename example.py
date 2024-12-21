import asyncio
import os
from dotenv import load_dotenv

from chapterize.transcribe import BookTranscriber

# Load environment variables from .env file
load_dotenv()

async def main():

    # Setup a transcriber
    bt = BookTranscriber(os.getenv("INPUT_DIRECTORY"))

    # Transcribe the file(s) please
    await bt.transcribe()


    # Your async code here
    print("Running async main function")
    await asyncio.sleep(1)
    print("Finished async main function")

if __name__ == "__main__":
    asyncio.run(main())