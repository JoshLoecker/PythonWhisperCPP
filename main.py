import os
import argparse
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from whisper import Whisper

@dataclass
class Arguments:
    """
    Define type-hinted arguments for the command line
    From: https://stackoverflow.com/a/71035314
    """
    model_path: Path
    ffmpeg_threads: int
    whisper_threads: int
    input: Path
    force_creation: bool
    executable: Path
    is_file: bool = None  # Will be evaluated at __post_init__
    video_extensions: tuple[str] = (".mp4", ".mkv", ".avi", ".webm")
    
    def __post_init__(self):
        
        # Determine if the input is a file or a directory
        if self.input.is_file():
            # Make sure the input file contains a video extension
            if self.input.suffix not in [".mp4", ".mkv", ".avi", ".webm"]:
                raise ValueError(f"Input file {self.input} does not have a valid video extension.\nValid extensions are: .mp4, .mkv, .avi, .webm")
            self.is_file = True
        else:
            self.is_file = False
            
        # Make sure the executable exists
        if self.executable is None:
        
            # Search in the parent directory of the model_path for an executable file
            for file in self.model_path.parent.parent.glob("*"):
                
                # Test if the file is a file, and if the file has executable permisssions
                if file.is_file() and os.access(file, os.X_OK):
                    self.executable = file
                    break
            

def parse_args() -> Arguments:
    parser = argparse.ArgumentParser(
        description="Create subtitles for a video file using WhisperCPP",
        # formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-m", "--model",
        required=True,
        dest="model_path",
        type=Path,
        metavar="model",
        help="The path to the model file"
    )
    parser.add_argument(
        "-e", "--executable",
        required=False,
        default=None,
        dest="executable",
        metavar="executable",
        help="The path to the whisper.cpp executable (defaults to `main` under the model parent directory)"
    )
    parser.add_argument(
        "-wt", "--whisper-threads",
        required=False,
        default=os.cpu_count(),
        dest="whisper_threads",
        metavar="threads",
        type=int,
        help=f"The number of threads to use for the whisper.cpp executable (default: {os.cpu_count()} for your system)"
    )
    parser.add_argument(
        "-ft", "--ffmpeg-threads",
        required=False,
        default=2,
        dest="ffmpeg_threads",
        metavar="threads",
        type=int,
        help="The number of threads to use for ffmpeg (default: 2)"
    )
    parser.add_argument(
        "--force",
        required=False,
        default=False,
        dest="force_creation",
        action="store_true",
        help="Force the creation of the subtitles even if they already exist"
    )
    
    # One of the two optins below is required
    path = parser.add_mutually_exclusive_group(required=True)
    path.add_argument(
        "-f", "--file",
        dest="input",
        type=Path,
        metavar="file",
        help="The path to the video file"
    )
    path.add_argument(
        "-d", "--directory",
        dest="input",
        type=Path,
        metavar="directory",
        help="The path to the directory containing video files"
    )
    args = Arguments(**vars(parser.parse_args()))
    return args

def main():
    args = parse_args()
    
    print(f"Found whisper.cpp executable at {args.executable}")
    
    whisper = Whisper(
        whisper_executable=args.executable,
        model_path=args.model_path,
        ffmpeg_threads=args.ffmpeg_threads,
        whisper_threads=args.whisper_threads,
        force_creation=args.force_creation
    )
    
    if args.is_file:
        whisper.create_subtitles(args.input)
    else:
        for file in args.input.iterdir():
            if file.suffix in args.video_extensions:
                whisper.create_subtitles(file)
    
    
if __name__ == '__main__':
    main()
