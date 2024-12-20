import os
import re
import argparse
from glob import glob
from pathlib import Path
from faster_whisper import WhisperModel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn
from rich.progress import BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel
import time
from datetime import timedelta
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich.text import Text

class Chapterizer:
    def __init__(self, base_dir, model_type="base", device="cpu", compute_type="int8", num_workers=4):
        """Initialize the Chapterizer with configuration."""
        self.console = Console()
        self.base_dir = Path(base_dir)
        self.model_type = model_type
        self.device = device
        self.compute_type = compute_type
        self.num_workers = num_workers
        self.model = None

        # Track processing statistics
        self.skipped_files = []
        self.partial_files = []
        self.unprocessed_files = []
        self.failed_files = []

        # Initialize layout components
        self.layout = Layout()
        self.status_table = Table.grid(padding=(0, 1))
        self.status_table.add_column()
        self.current_file = None
        self.detected_chapters = []

    def format_timestamp(self, seconds):
        """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
        td = timedelta(seconds=seconds)
        hours = td.seconds//3600
        minutes = (td.seconds//60)%60
        seconds = td.seconds%60
        milliseconds = round(td.microseconds/1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def validate_srt(self, file_path, expected_duration):
        """Validate if SRT file is complete and properly formatted"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                if not content:
                    return False

                if not content.endswith('\n\n'):
                    return False

                lines = content.split('\n')
                for line in reversed(lines):
                    if ' --> ' in line:
                        end_time = line.split(' --> ')[1].strip()
                        h, m, s = end_time.split(',')[0].split(':')
                        last_timestamp = int(h) * 3600 + int(m) * 60 + int(s)

                        if abs(last_timestamp - expected_duration) > 30:
                            return False
                        break

                return True
        except Exception as e:
            self.console.print(f"[red]Error validating {file_path}: {str(e)}[/]")
            return False

    def is_chapter_title(self, text):
        """Enhanced chapter detection with common patterns"""
        text_lower = text.lower().strip()

        # Common chapter patterns
        patterns = [
            r'^chapter\s+\d+',
            r'^book\s+\d+',
            r'^part\s+\d+',
            r'^section\s+\d+',
            r'^volume\s+\d+',
            r'^epilogue',
            r'^prologue',
            r'^introduction',
            r'^preface',
            r'^appendix',
            r'^afterword',
            r'^interlude',
            r'^act\s+\d+',
            r'^\d+\.',  # Numbered chapters without "chapter"
            r'book\s+\d+:\s+chapter',
        ]

        # Special phrases
        special_phrases = [
            'read for you by',
            'end of chapter',
            'end of book',
            'end of part'
        ]

        # Check against regex patterns
        if any(re.match(pattern, text_lower) for pattern in patterns):
            return True

        # Check against special phrases
        if any(phrase in text_lower for phrase in special_phrases):
            return True

        # Check for numbered patterns
        if re.match(r'^\d+\s*$', text_lower):  # Just a number
            return True

        return False

    def find_audio_files(self):
        """Recursively find all MP3 files in the base directory."""
        return sorted(self.base_dir.rglob("*.mp3"))

    def initialize_model(self):
        """Initialize the Whisper model."""
        with self.console.status("[bold blue]Loading Whisper model...", spinner="dots"):
            self.model = WhisperModel(
                self.model_type,
                device=self.device,
                compute_type=self.compute_type,
                num_workers=self.num_workers,
            )
        self.console.print("[bold green]Model loaded successfully! ✓[/]")

    def categorize_files(self):
        """Categorize files as unprocessed, partial, or complete."""
        audio_files = self.find_audio_files()

        for audio_file in audio_files:
            base_name = audio_file.stem
            srt_path = audio_file.with_suffix('.srt')

            if srt_path.exists():
                with self.console.status(f"[yellow]Checking {base_name}...", spinner="dots"):
                    _, info = self.model.transcribe(str(audio_file), language="en")
                    expected_duration = round(info.duration)

                    if self.validate_srt(srt_path, expected_duration):
                        self.skipped_files.append(audio_file)
                    else:
                        self.partial_files.append(audio_file)
                        self.unprocessed_files.append(audio_file)
            else:
                self.unprocessed_files.append(audio_file)

    def create_layout(self):
        """Create the layout for the Live display"""
        self.layout.split_column(
            Layout(name="progress", size=2),
            Layout(name="chapters", size=3),
            Layout(name="stats", size=2)
        )

    def update_layout(self, progress_text, chapters, stats):
        """Update the layout with current information"""
        self.layout["progress"].update(Panel(progress_text))
        self.layout["chapters"].update(Panel("\n".join(chapters) if chapters else "No chapters detected yet"))
        self.layout["stats"].update(Panel(stats))

    def process_file(self, audio_file, progress, file_task):
        """Process a single audio file and create SRT output."""
        try:
            base_name = audio_file.stem
            output_path = audio_file.with_suffix('.srt')
            chapters_found = []

            # Modified transcription parameters
            segments, info = self.model.transcribe(
                str(audio_file),
                word_timestamps=True,
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=1000,
                    speech_pad_ms=400,
                ),
                condition_on_previous_text=True,
                initial_prompt="This is an audiobook with chapters."
            )

            total_duration = round(info.duration)
            progress.update(file_task,
                            total=total_duration,
                            completed=0,
                            visible=True,
                            description=f"[cyan]Processing {base_name}")

            start_time = time.time()
            last_update_time = time.time()
            last_timestamp = 0

            segments_list = list(segments)

            with Live(self.layout, refresh_per_second=4) as live:
                with open(output_path, 'w', encoding='utf-8') as f:
                    current_chapter = None

                    for i, segment in enumerate(segments_list, 1):
                        text = segment.text.strip()

                        # Chapter detection
                        if self.is_chapter_title(text):
                            current_chapter = text
                            chapters_found.append(f"[yellow]Chapter detected: {text}[/]")

                            # Update layout less frequently to prevent flicker
                            current_time = time.time()
                            if current_time - last_update_time > 0.25:  # Update max 4 times per second
                                self.update_layout(
                                    f"Processing {base_name}\n{progress}",
                                    chapters_found[-5:],  # Show last 5 chapters
                                    f"Progress: {round(segment.end/total_duration * 100)}%"
                                )
                                last_update_time = current_time

                        # Write SRT entry
                        f.write(f"{i}\n")
                        f.write(f"{self.format_timestamp(segment.start)} --> {self.format_timestamp(segment.end)}\n")

                        if current_chapter and text in current_chapter:
                            f.write(f"[CHAPTER] {text}\n")
                        else:
                            f.write(f"{text}\n")

                        f.write("\n")

                        current_timestamp = round(segment.end)
                        if current_timestamp > last_timestamp:
                            progress.update(file_task, completed=current_timestamp)
                            last_timestamp = current_timestamp

            if last_timestamp < total_duration:
                progress.update(file_task, completed=total_duration)

            duration = time.time() - start_time
            speed = round(total_duration / duration, 2)
            self.console.print(f"[green]Processed at {speed}x real-time speed[/]")

            # Display final chapters
            if chapters_found:
                self.console.print(Panel("\n".join(chapters_found), title="Detected Chapters"))

            return True

        except Exception as e:
            self.console.print(f"[red]Error processing {base_name}: {str(e)}[/]")
            self.failed_files.append(audio_file)
            return False

    def run(self):
        """Main execution method."""
        self.initialize_model()
        self.categorize_files()
        self.create_layout()

        total_files = len(self.unprocessed_files)

        if self.skipped_files:
            self.console.print(Panel(f"[yellow]Skipping {len(self.skipped_files)} properly processed files:[/]\n" +
                                     "\n".join(f"- {f.stem}" for f in self.skipped_files)))

        if self.partial_files:
            self.console.print(Panel(f"[red]Found {len(self.partial_files)} partially processed files (will reprocess):[/]\n" +
                                     "\n".join(f"- {f.stem}" for f in self.partial_files)))

        self.console.print(Panel(f"[bold green]Found {total_files} files to process[/]"))

        if total_files == 0:
            self.console.print("[bold blue]All files have been processed already! ✨[/]")
            return

        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
        ) as progress:
            overall_task = progress.add_task("[cyan]Overall progress", total=total_files)
            file_task = progress.add_task("[cyan]Current file", visible=False)

            for audio_file in self.unprocessed_files:
                if self.process_file(audio_file, progress, file_task):
                    progress.advance(overall_task)
                progress.update(file_task, visible=False)

        if self.failed_files:
            self.console.print(Panel(f"[red]Failed to process {len(self.failed_files)} files:[/]\n" +
                                     "\n".join(f"- {f.stem}" for f in self.failed_files)))

        self.console.print("[bold green]Transcription completed! 🎉[/]")

def main():
    parser = argparse.ArgumentParser(description='Process audio files to generate SRT files')
    parser.add_argument('directory', help='Directory containing audio files to process')
    parser.add_argument('--model', default='base', help='Whisper model type (default: base)')
    parser.add_argument('--device', default='cpu', help='Processing device (default: cpu)')
    parser.add_argument('--compute-type', default='int8', help='Compute type (default: int8)')
    parser.add_argument('--workers', type=int, default=4, help='Number of workers (default: 4)')

    args = parser.parse_args()

    chapterizer = Chapterizer(
        args.directory,
        model_type=args.model,
        device=args.device,
        compute_type=args.compute_type,
        num_workers=args.workers
    )
    chapterizer.run()

if __name__ == "__main__":
    main()