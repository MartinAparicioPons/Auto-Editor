import argparse
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment, silence

# Program arguments
SILENCE_THRESHOLD = None                            # Shorten only silences longer than this (ms)
PADDING_LEFT = None                                 # Padding before speech (in ms)
PADDING_RIGHT = None                                # Padding after speech (in ms)
SILENCE_DB_THRESHOLD = None                         # dB Threshold of what's considered silence
VERBOSE = None                                      # Will print more stuff when working
DEBUG = None                                        # Will print debug stuff when working
INPUT_PATH = None                                   # Input video path
OUTPUT_PATH = None                                  # Output video path

# Constants
AUDIO_CODEC = 'pcm_s16le'                           # Codec used for audio processing
OUTPUT_VIDEO_CODEC = "libx264"                      # Codec used for final video
OUTPUT_AUDIO_CODEC = "aac"                          # Codec for audio in the final video
TEMP_AUDIO_PATH = "temp_audio.wav"                  # Path for temporarily saved audio
TEMP_EDITED_AUDIO_PATH = 'temp_edited_audio.wav'    # Path for temporarily saved audio after edition


def verbose_print(string, args = None):
    """Prints only if on VERBOSE mode"""
    if VERBOSE:
        if args is None:
            args = []
        print(string.format(*args))

def debug_print(string, args = None):
    """Prints only if on DEBUG mode"""
    if DEBUG:
        if args is None:
            args = []
        print(string.format(*args))

def extract_audio_from_video(video_path):
    """Extracts the audio from the given video file and returns it as an AudioSegment."""
    verbose_print("Extracting audio from video")
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(TEMP_AUDIO_PATH, codec=AUDIO_CODEC)  # Save extracted audio
    audio_segment = AudioSegment.from_wav(TEMP_AUDIO_PATH)
    return audio_segment

def iterate_silence_segments(silent_ranges, video, audio_segment, pretend = True):
    """
        Iterate over all the silence ranges found and calculate the final length of the edited 
        video if in pretend mode. If not in pretend mode, return the clips to keep and the audio separately.
    """
    # Track end of last segment
    last_end = 0
    clips = []
    # A bit of a hack to get an empty AudioSegment
    adjusted_audio = audio_segment[:0]
    silence_amount = 0

    for start, end in silent_ranges:
        # Add non-silence audio/video before the current silence
        end_clip = max(last_end, start - PADDING_LEFT)
        if last_end / 1000 < end_clip / 1000:
            debug_print("Will add the clip from {} to {} ({}ms)", [last_end / 1000, end_clip / 1000, end_clip - last_end])
            if not pretend:
                clips.append(video.subclip(last_end / 1000, end_clip / 1000))
                adjusted_audio += audio_segment[last_end:max(last_end, start - PADDING_LEFT)]

        silence_duration = end - end_clip
        debug_print("Will cut the silence from {} to {} ({}ms)", [end_clip / 1000, (end - PADDING_RIGHT) / 1000, silence_duration])

        # Discard silences that are smaller than the threshold
        if silence_duration > SILENCE_THRESHOLD:
            last_end = end - PADDING_RIGHT
            silence_amount += last_end - end_clip
        else:
            last_end = end_clip

    if not pretend:
        # Append the remaining parts of the video and audio
        clips.append(video.subclip(last_end / 1000.0, video.duration))
        adjusted_audio += audio_segment[last_end:]
    return (clips, adjusted_audio, silence_amount)

def edit_video_and_audio(video_path, audio_segment):
    """Process the video and audio to remove silences and write to a new file"""
    verbose_print("Starting edit_video_and_audio")
    video = VideoFileClip(video_path)

    # Find silent sections in the audio
    silent_ranges = silence.detect_silence(audio_segment, min_silence_len=SILENCE_THRESHOLD, silence_thresh=SILENCE_DB_THRESHOLD)

    verbose_print("Silences found: {}", [str(len(silent_ranges))])
    debug_print(silent_ranges)

    # Iterate in pretend mode to get the silence amount 
    _, _ , silence_amount = iterate_silence_segments(silent_ranges=silent_ranges, video=video, audio_segment=audio_segment, pretend=True)

    print(f"\nWould end up with a video {len(audio_segment)/1000 - silence_amount / 1000}s long, cutting from the original {len(audio_segment)/1000}s. \n")
    print(f"Would be {silence_amount / 1000}s shorter")
    user_response = input("Do you want to render the video? Y/N\n").strip().upper()

    if user_response == "Y":
        # Iterate for real this time, get the clips and audio
        clips, adjusted_audio, _ = iterate_silence_segments(silent_ranges=silent_ranges, video=video, audio_segment=audio_segment, pretend=False)

        # Combine all clips into a new video
        final_video = concatenate_videoclips(clips)

        # Save the edited audio back to a file
        adjusted_audio.export(TEMP_EDITED_AUDIO_PATH, format='wav')

        # Store the audio into a temp file to get the AudioClip
        edited_audio_clip = AudioFileClip(TEMP_EDITED_AUDIO_PATH)
        final_video = final_video.set_audio(edited_audio_clip)

        # Write the final video onto the output path
        final_video.write_videofile(OUTPUT_PATH, codec=OUTPUT_VIDEO_CODEC, audio_codec=OUTPUT_AUDIO_CODEC)
    try:
        if os.path.isfile(TEMP_EDITED_AUDIO_PATH):
            os.remove(TEMP_EDITED_AUDIO_PATH)
        if os.path.isfile(TEMP_AUDIO_PATH):
            os.remove(TEMP_AUDIO_PATH)
    except OSError:
        print("Couldn't clean up the audio temp file")


def main():
    global INPUT_PATH, OUTPUT_PATH, SILENCE_THRESHOLD, PADDING_LEFT, PADDING_RIGHT, SILENCE_DB_THRESHOLD, VERBOSE, DEBUG

    parser = argparse.ArgumentParser(description='Remove silences from video.')

    # Mandatory positional arguments
    parser.add_argument('input_path', type=str, help='Input video path')
    parser.add_argument('output_path', type=str, help='Output video path')

    # Optional arguments
    parser.add_argument('--silence_threshold', type=int, default=700, help='Minimum silence to cut in ms')
    parser.add_argument('--padding_left', type=int, default=250, help='Padding before cutoff from left side')
    parser.add_argument('--padding_right', type=int, default=250, help='Padding before cutoff from right side')
    parser.add_argument('--silence_db_threshold', type=int, default=-40, help='Threshold in dB to consider a silence')
    parser.add_argument('--verbose', type=bool, default=False, help='Verbose mode (True/False)')
    parser.add_argument('--debug', type=bool, default=False, help='Debug mode (True/False)')

    args = parser.parse_args()

    INPUT_PATH = args.input_path
    OUTPUT_PATH = args.output_path
    SILENCE_THRESHOLD = args.silence_threshold
    PADDING_LEFT = args.padding_left
    PADDING_RIGHT = args.padding_right
    SILENCE_DB_THRESHOLD = args.silence_db_threshold
    VERBOSE = args.verbose
    DEBUG = args.debug

    audio_segment = extract_audio_from_video(INPUT_PATH)
    edit_video_and_audio(INPUT_PATH, audio_segment)

if __name__ == '__main__':
    main()
