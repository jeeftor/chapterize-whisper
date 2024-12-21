import os
from glob import glob

import aiofiles
import asyncio
from faster_whisper import WhisperModel, BatchedInferencePipeline
from faster_whisper.transcribe import Segment, TranscriptionInfo
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, SpinnerColumn
from rich.live import Live
from rich.console import Console  # Changed this line

# https://api.audiobookshelf.org/#update-a-library-item-39-s-audio-tracks
#POST http://abs.example.com/api/items/<ID>/chapters
#curl -X POST "https://abs.example.com/api/items/li_bufnnmp4y5o2gbbxfm/chapters" \
#-H "Authorization: Bearer exJhbGciOiJI6IkpXVCJ9.eyJ1c2Vyi5NDEyODc4fQ.ZraBFohS4Tg39NszY" \
#   -H "Content-Type: application/json" \
#      -d '{"chapters": [{"id": 0, "start": 0, "end": 6004.6675, "title": "Terry Goodkind - SOT Bk01 - Wizards First Rule 01"}, {"id": 1, "start": 6004.6675, "end": 12000.946, "title": "Terry Goodkind - SOT Bk01 - Wizards First Rule 02"}]}'


#id	Integer	The ID of the book chapter.
#start	Float	When in the book (in seconds) the chapter starts.
#end	Float	When in the book (in seconds) the chapter ends.
#title	String	The title of the chapter.

from chapterize.utils import is_chapter, format_timestamp_srt

console = Console()

class FileTranscriber:
    def __init__(self, audio_file: str) -> None:
        self.batch_info = None
        self.info = None
        self.audio_file = audio_file
        self.audio_directory = os.path.dirname(audio_file)
        self.segments = None
        self.batch_segments = None
        self.model: WhisperModel = WhisperModel(
            "tiny.en",
            device="cpu",
            compute_type="int8",
            num_workers=8
        )
        self.model.beam_size = 5
        self.model.vad_filter = True
        self.model.vad_parameters = {
            "min_silence_duration_ms": 1000,
            "speech_pad_ms": 400,
        }
        self.model.condition_on_previous_text = True
        self.model.initial_prompt = "This is an audiobook with chapters."
        self.batched_model: BatchedInferencePipeline = BatchedInferencePipeline(self.model)


    async def _process_segment(self, segment: Segment, segment_number: int, offset: float):
        if is_chapter(segment.text):
            print(f"CHAPTER MAYBE DETECTED:: {segment.text}")
            async with aiofiles.open(f'{self.audio_directory}/transcription.chapters', 'a', encoding='utf-8') as f:
                await f.write(f"{segment.start + offset}, {segment.text}\n")


        # Write to an output file
        async with aiofiles.open(f'{self.audio_directory}/transcription.srt', 'a', encoding='utf-8') as f:
            start_time = format_timestamp_srt(segment.start, offset)
            end_time = format_timestamp_srt(segment.end, offset)
            await f.write(f"{segment_number}\n{start_time} --> {end_time}\n{(segment.text.strip())}\n\n")


    # async def batch_transcribe(self, batch_size: int = 32) -> TranscriptionInfo:
    #     segments, info = self.batched_model.transcribe(self.audio_file, batch_size=batch_size)
    #     async with aiofiles.open(f'{self.audio_directory}.srt', 'w', encoding='utf-8') as f:
    #         for segment in segments:
    #             percent = round((segment.end / info.duration * 100), 1)
    #             await f.write(f"{percent}% - {segment.text}\n")
    #             print(f"{percent}% {segment.text}")
    #     return info
    # async def transcribe(self) -> TranscriptionInfo:
    #     segments, info = self.model.transcribe(self.audio_file)
    #     async with aiofiles.open(f'{self.audio_directory}.srt', 'w', encoding='utf-8') as f:
    #         for segment in segments:
    #             percent = round((segment.end / info.duration * 100), 1)
    #             await f.write(f"{percent}% - {segment.text}\n")
    #             print(f"{percent}% {segment.text}")
    #     return info

    async def transcribe_with_progress(self, offset_index: int = 0, offset_seconds:float = 0.0)  -> tuple[int, float]:

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=50),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            TextColumn("[bold]{task.fields[status]}"),
            console=console  # Using the console you already defined at module level
        )
        with Live(progress, refresh_per_second=10):
            task = progress.add_task(f"{self.audio_file}", total=100, status="Starting...")
            segments, info = self.model.transcribe(self.audio_file)

            async with aiofiles.open(f'{self.audio_file}.srt', 'w', encoding='utf-8') as f:
                for index, segment in enumerate(segments, 1):
                    percent = round((segment.end / info.duration * 100), 1)
                    await self._process_segment(segment, index + offset_index, offset_seconds)
                # Update progress with current segment text
                    progress.update(
                        task,
                        completed=percent,
                        status=f"Transcribing: {segment.text[:50]}..."
                    )
        return index, info.duration

class BookTranscriber:
    def __init__(self, directory: str) -> None:
        self.directory = directory
        self.audio_files = self._get_audio_files()
        self._clean_detection_files()

    def _clean_detection_files(self):
        console.print("Cleaning up detection files...")
        for audio_file in self.audio_files:
            for ext in ['srt', 'chapters']:
                try:
                    os.remove(f'{audio_file}.{ext}')
                    console.print(f"Removed {audio_file}.{ext}")
                except FileNotFoundError:
                    pass

    def _get_audio_files(self) -> list:
        # Define the audio file extensions to look for
        audio_extensions = ['*.mp3', '*.ogg', '*.m4a', '*.wav', '*.flac']
        audio_files = []

        # Search for audio files with the specified extensions
        for ext in audio_extensions:
            audio_files.extend(glob(os.path.join(self.directory, ext)))

        # Sort the audio files
        audio_files.sort()
        return audio_files




# Example usage
if __name__ == "__main__":
    bt = BookTranscriber("../data")
    offset_seconds = 0.0
    offset_index = 0

    for audio_file in bt.audio_files:
        t = FileTranscriber(audio_file)
        offset_seconds, offset_index = asyncio.run(t.transcribe_with_progress(offset_index, offset_seconds))
        console.print(f"Transcribed {audio_file} with {offset_index} segments and {offset_seconds} seconds offset.")



