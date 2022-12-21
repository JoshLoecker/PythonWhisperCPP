import os
import argparse
from pathlib import Path
from dataclasses import dataclass
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
    dry_run: bool
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
    parser.add_argument(
        "-n", "--dry-run",
        required=False,
        default=False,
        dest="dry_run",
        action="store_true",
        help="Do not execute whisper.cpp, only show what would be performed. Useful to ensure everything is set up properly"
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
    
    whisper = Whisper(
        whisper_executable=args.executable,
        model_path=args.model_path,
        ffmpeg_threads=args.ffmpeg_threads,
        whisper_threads=args.whisper_threads,
        force_creation=args.force_creation
    )
    
    # Collect input files
    input_files: list[Path] = []
    if args.is_file:
        input_files.append(args.input)
    else:
        # Recursively collect files in the input directory
        input_files = [file for file in args.input.rglob("*") if file.is_file() and file.suffix in args.video_extensions]
    
    # Create subtitles for each input file if not a dry run
    to_create: int = 0
    exists: int = 0
    for file in input_files:
        if args.dry_run:
            if Whisper.should_create_srt(input_file=file, force=args.force_creation):
                print(f"CREATE:\t{file.with_suffix('.en.srt')}")
                to_create += 1
            else:
                print(f"EXISTS:\t{file.with_suffix('.en.srt')}")
                exists += 1
        else:
            whisper.create_subtitles(file)
            print("")
    
    if args.dry_run:
        # Create a simple table of the results
        print("\n")
        print(f"{'='*10} RESULTS {'='*10}")
        print(f"{'To Create:':<10} {to_create}")
        print(f"{'Existing:':<10} {exists}")
        print(f"{'='*29}")
        
    
    
if __name__ == '__main__':
    main()
