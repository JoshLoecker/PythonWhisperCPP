import os
import shutil
import subprocess
from pathlib import Path

class Whisper:
    temp_path: Path = Path("/tmp")
    
    def __init__(
            self,
            whisper_executable: str | Path,
            model_path: str | Path,
            force_creation: bool,
            ffmpeg_threads: int = 2,
            whisper_threads: int = os.cpu_count() // 2,
    ):
        self._whisper_executable: Path = whisper_executable
        self._model_path: Path = model_path
        self._force_creation: bool = force_creation
        
        if ffmpeg_threads > os.cpu_count():
            print("WARNING: ffmpeg_threads is greater than the number of CPU cores. Setting ffmpeg_threads to the number of CPU cores.")
            self._ffmpeg_threads: int = os.cpu_count()
        else:
            self._ffmpeg_threads: int = ffmpeg_threads
        
        if whisper_threads > os.cpu_count():
            print("WARNING: whisper_threads is greater than the number of CPU cores. Setting whisper_threads to the number of CPU cores.")
            self._whisper_threads: int = os.cpu_count()
        else:
            self._whisper_threads: int = whisper_threads
        
        # These will be set when create_subtitles is called
        self._input_file: Path = Path()
        self._temp_wav_file: Path = Path()
        self._temp_srt_file: Path = Path()
        self._log_file: Path = Path()
        self._final_srt_file: Path = Path()
    
    @classmethod
    def _get_temp_wav_path(cls, file: str | Path) -> Path:
        return Path(Whisper.temp_path / f"{Path(file).stem}.wav")
    @classmethod
    def _get_temp_srt_path(cls, file: str | Path) -> Path:
        return Path(Whisper.temp_path / f"{Path(file).stem}.wav.srt")
    @classmethod
    def _get_final_srt_file(cls, file: str | Path) -> Path:
        return Path(file.parent / f"{file.stem}.en.srt")
        # return self._input_file.parent / f"{self._input_file.stem}.en.srt"
        
    def _set_input_file(self, input_file: str | Path) -> None:
        self._input_file = Path(input_file)
        
        self._log_file = Path(f"logs/{self._input_file.stem}.log")
        self._temp_wav_file = self._get_temp_wav_path(input_file)
        self._temp_srt_file = self._get_temp_srt_path(input_file)
        self._final_srt_file = self._get_final_srt_file(input_file)
        os.makedirs(self._log_file.parent, exist_ok=True)
    
    def cleanup(self):
        """
        Remove the temporary files created by this class
        """
        self._temp_wav_file.unlink(missing_ok=True)
    
    def create_subtitles(
            self,
            input_file: str | Path,
            print_colors: bool = True,
            output_srt: bool = True,
            remove_temp_files: bool = True
    ):
        self._set_input_file(input_file)
        print("Input files set")
        if not self._final_srt_file.exists() or self._force_creation:  # If the SRT file doesn't exist OR force_creation is True, create the SRT file
            log_write = open(self._log_file, "w")
            self._create_wav()
            print(f"CREATE:\t{self._final_srt_file}")
            subprocess.run(
                args=[
                    str(self._whisper_executable),
                    "--model", str(self._model_path),
                    "--print-colors" if print_colors else "",
                    "--output-srt" if output_srt else "",
                    "--threads", str(self._whisper_threads),
                    "--file", str(self._temp_wav_file)
                ],
                stdout=log_write,
                stderr=log_write
            )
            log_write.close()

            # Move the SRT file to the final location
            shutil.move(self._temp_srt_file, self._final_srt_file)

            # Move the self._srt_file to the same directory as the input file
            if remove_temp_files:
                self.cleanup()
            
        else:
            print(f"SKIP:\t{self._final_srt_file.stem}.srt is present")

    def _create_wav(self):
        """
        This function is responsible for using ffmpeg to create a 16-bit WAV file, which is required by whisper.
        From: https://github.com/ggerganov/whisper.cpp
        """
        if self._temp_wav_file.exists():
            # Remove the WAV file
            self._temp_wav_file.unlink()
            
        print(f"WAV:\t{self._temp_wav_file}")
        # Use ffmpeg to create a 16-bit WAV file
        subprocess.run(args=[
            "ffmpeg",
            "-loglevel", "quiet",
            "-threads", str(self._ffmpeg_threads),
            "-i", self._input_file,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            self._temp_wav_file
        ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
            
    @property
    def srt_file(self) -> Path:
        # subtitle_path = self._input_file.parent / f"{self._input_file.stem}.srt"
        subtitle_path: Path = self._temp_wav_file.parent / f"{self._temp_wav_file.stem}.srt"
        return subtitle_path

    @classmethod
    def should_create_wav(cls, input_file: str | Path) -> bool:
        input_file = Path(input_file)  # Ensure input is a Path object
        
        wav_file: Path = cls._get_temp_wav_path(input_file)
        if wav_file.exists():
            return False
        else:
            return True

    @classmethod
    def should_create_srt(cls, input_file: str | Path) -> bool:
        input_file = Path(input_file)
        
        srt_file: Path = cls._get_final_srt_file(input_file)
        if srt_file.exists():
            return False
        else:
            return True
        
