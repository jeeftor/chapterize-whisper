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
    def __init__(self,
                 audio_file: str,
                 model: str = "tiny.en",
                 device: str = "auto",
                 num_workers: int = 8,
                 cpu_threads: int = 0) -> None:
        self.batch_info = None
        self.info = None
        self.audio_file = audio_file
        self.audio_directory = os.path.dirname(audio_file)
        self.parent_directory = os.path.basename(self.audio_directory)

        self.chapter_file = os.path.join(self.audio_directory, self.parent_directory + ".chapters")
        self.srt_file = os.path.join(self.audio_directory, self.parent_directory + ".srt")
        self.batch_srt_file = os.path.join(self.audio_directory, self.parent_directory + ".batch.srt")

        self.segments = None
        self.batch_segments = None
        self.model: WhisperModel = WhisperModel(
            model,
            device=device,
            compute_type="int8",
            num_workers=num_workers,
            cpu_threads=cpu_threads
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


    async def _process_segment(self, segment: Segment, segment_number: int, offset: float, is_batch: bool = False) -> None:

        if segment_number == 0:
            # First Segment
            async with aiofiles.open(self.chapter_file, 'a', encoding='utf-8') as f:
                await f.write(f"00:00:00,0000, BOOK Start\n")


        if is_chapter(segment.text):
            time_hms = format_timestamp_srt(segment.start, offset)
            print(f"Possible Chapter [{time_hms}] : {segment.text}")
            async with aiofiles.open(self.chapter_file, 'a', encoding='utf-8') as f:
                await f.write(f"{time_hms}, {segment.text}\n")

        start_time = format_timestamp_srt(segment.start, offset)
        end_time = format_timestamp_srt(segment.end, offset)

        if is_batch:
            # This needs to be sorted when done.
            async with aiofiles.open(self.batch_srt_file, 'a', encoding='utf-8') as f:
                await f.write(f"{segment_number}\n{start_time} --> {end_time}\n{(segment.text.strip())}\n\n")

        else:
            # Write to an output file
            async with aiofiles.open(self.srt_file, 'a', encoding='utf-8') as f:
                await f.write(f"{segment_number}\n{start_time} --> {end_time}\n{(segment.text.strip())}\n\n")



    async def batch_transcribe_with_progress(self, offset_index: int = 0, offset_seconds:float = 0.0)  -> tuple[int, float]:
        console.print("Starting Batch transcription of audio files...")
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
            segments, info = self.batched_model.transcribe(self.audio_file)

            for index, segment in enumerate(segments, offset_index):
                percent = round((segment.end / info.duration * 100), 1)
                await self._process_segment(segment, index, offset_seconds, is_batch=True)
                # Update progress with current segment text
                progress.update(
                    task,
                    completed=percent,
                    status=f"Transcribing: {segment.text[:50]}..."
                )

        return index, info.duration



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

            for index, segment in enumerate(segments, offset_index):
                percent = round((segment.end / info.duration * 100), 1)
                await self._process_segment(segment, index, offset_seconds, is_batch=False)
                # Update progress with current segment text
                progress.update(
                    task,
                    completed=percent,
                    status=f"Transcribing: {segment.text[:50]}..."
                )
        return index + 1, info.duration + offset_seconds

class BookTranscriber:
    def __init__(self, directory: str, model: str = 'tiny.en', device: str = 'auto',
                 num_workers: int = 8, cpu_threads: int = 0) -> None:
        self.directory = directory
        self.model_config = {
            'model': model,
            'device': device,
            'num_workers': num_workers,
            'cpu_threads': cpu_threads
        }
        self.audio_files = self._get_audio_files()
        self._clean_detection_files()
        console.print(f"Found {len(self.audio_files)} audio files in {self.directory}")

    def _clean_detection_files(self):
        console.print("Cleaning up detection files...")
        for transcription_file in self._get_transcription_files():
            try:
                os.remove(f'{transcription_file}')
                console.print(f"Removed {transcription_file}")
            except FileNotFoundError:
                pass

    def _get_transcription_files(self) -> list:
        # Define the audio file extensions to look for
        audio_extensions = ['**/*.srt', '**/*.chapters']
        audio_files = []

        # Search for audio files with the specified extensions
        for ext in audio_extensions:
            audio_files.extend(glob(os.path.join(self.directory, ext)))

        # Sort the audio files
        audio_files.sort()
        return audio_files


    def _get_audio_files(self) -> list:
        # Define the audio file extensions to look for
        audio_extensions = ['**/*.mp3', '**/*.ogg', '**/*.m4a', '**/*.wav', '**/*.flac', '**/*.m4b']
        audio_files = []

        # Search for audio files with the specified extensions
        for ext in audio_extensions:
            audio_files.extend(glob(os.path.join(self.directory, ext), recursive=True))

        # Sort the audio files
        audio_files.sort()
        return audio_files


    async def transcribe(self) -> None:
        offset_seconds: float = 0.0
        offset_index: int = 0


        for audio_file in self.audio_files:
            t = FileTranscriber(audio_file)
            console.print(f"Transcribing with offset {offset_index} and index {offset_index}")
            offset_index, offset_seconds = await t.transcribe_with_progress(offset_index, offset_seconds)
            console.print(f"Transcribed {audio_file} with {offset_index} segments and {offset_seconds} seconds offset.")
            chapter_file = t.chapter_file

        # When we are done the final info is:
        book_duration = offset_seconds

        # Write the duration to the chapter files.
        async with aiofiles.open(chapter_file, 'a', encoding='utf-8') as f:
            await f.write(f"{format_timestamp_srt(book_duration,0)}, BOOK_END\n")


        console.print(f"Finished transcription. Please review {chapter_file} for errors")
