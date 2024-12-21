from mutagen import File
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4  # For M4B files

class AudiobookMetadata:
    def __init__(self, filepath):
        self.filepath = filepath
        self.metadata = None
        self._load_metadata()

    def _load_metadata(self):
        # Auto-detect file type and load appropriate metadata
        self.metadata = File(self.filepath)

        if self.metadata is None:
            raise ValueError(f"Could not read metadata from {self.filepath}")

    def get_basic_info(self):
        # Common tags across formats
        info = {
            'title': None,
            'artist': None,
            'album': None,
            'duration': None,
            'chapters': None
        }

        if isinstance(self.metadata, MP4):
            # M4B specific handling
            tags = {
                'title': '\xa9nam',
                'artist': '\xa9ART',
                'album': '\xa9alb'
            }
            for key, tag in tags.items():
                if tag in self.metadata:
                    info[key] = self.metadata[tag][0]

            # Get duration in seconds
            info['duration'] = self.metadata.info.length

            # M4B chapter handling
            if 'chpl' in self.metadata:
                info['chapters'] = self.metadata['chpl']

        elif isinstance(self.metadata, MP3):
            # MP3 handling
            if self.metadata.tags:
                info['title'] = self.metadata.tags.get('TIT2', [''])[0]
                info['artist'] = self.metadata.tags.get('TPE1', [''])[0]
                info['album'] = self.metadata.tags.get('TALB', [''])[0]

            info['duration'] = self.metadata.info.length

        return info

