import os
from glob import glob
from faster_whisper import WhisperModel
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel
import time

console = Console()

# Get all MP3 files in the data directory and sort them
audio_files = sorted(glob('data/*.mp3'))

# Filter out already processed files
unprocessed_files = []
skipped_files = []

for audio_file in audio_files:
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    txt_path = f'data/{base_name}.txt'

    if not os.path.exists(txt_path):
        unprocessed_files.append(audio_file)
    else:
        skipped_files.append(base_name)

total_files = len(unprocessed_files)

if skipped_files:
    console.print(Panel(f"[yellow]Skipping {len(skipped_files)} already processed files:[/]\n" +
                        "\n".join(f"- {name}" for name in skipped_files)))

console.print(Panel(f"[bold green]Found {total_files} files to process[/]"))

if total_files == 0:
    console.print("[bold blue]All files have been processed already! ✨[/]")
    exit(0)

# Initialize the Whisper model with the specified parameters
with console.status("[bold blue]Loading Whisper model...", spinner="dots"):
    model = WhisperModel(
        "base",
        device="cpu",
        compute_type="int8",
        num_workers=4,
    )
console.print("[bold green]Model loaded successfully! ✓[/]")

# Create progress tracking for file processing
with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
) as progress:

    overall_task = progress.add_task("[cyan]Overall progress", total=len(unprocessed_files))
    file_task = progress.add_task("[cyan]Current file", visible=False)

    for audio_file in unprocessed_files:
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        output_path = f'data/{base_name}.txt'

        # First get the duration of the audio
        segments, info = model.transcribe(
            audio_file,
            word_timestamps=True,
            language="en",
            beam_size=5,
            vad_filter=True
        )

        # Set up the file progress bar with the total duration
        total_duration = round(info.duration)
        progress.update(file_task,
                        total=total_duration,
                        completed=0,
                        visible=True,
                        description=f"[cyan]Processing {base_name}")

        start_time = time.time()
        last_timestamp = 0

        # Open the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                # Write the segment
                f.write(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n")

                # Update progress based on segment timestamp
                current_timestamp = round(segment.end)
                if current_timestamp > last_timestamp:
                    progress.update(file_task, completed=current_timestamp)
                    last_timestamp = current_timestamp

        # Handle any silence at the end
        if last_timestamp < total_duration:
            progress.update(file_task, completed=total_duration)

        # Calculate and display speed
        duration = time.time() - start_time
        speed = round(total_duration / duration, 2)
        console.print(f"[green]Processed at {speed}x real-time speed[/]")