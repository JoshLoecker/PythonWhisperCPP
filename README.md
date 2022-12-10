# PythonWhisperCPP

This project uses the [WhisperCPP](https://github.com/ggerganov/whisper.cpp) project to create subtitles for videos.  
Please view the linked project above for setup and installation. This project will fail if the WhisperCPP project is not installed.


## Usage
Assuming you have a trained model (which ca be downloaded following the instructions from the WhisperCPP project), you can run the following command to generate subtitles for a video. Subtitles will be named the same name as the video inupt, replacing the extension with `.en.srt`. The subtitles will be generated in the same directory as the video.

    # Create subtitles for the videos under /videos
    python main.py --model model.pt --directory /videos --whisper-threads 4

    # Force creation of subtitles for a video, even if the subtitles already exist
    python main.py --force --model model.pt --file /videos/my_video.mp4 --whisper-threads 8

