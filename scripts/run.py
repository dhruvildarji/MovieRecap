import cv2
import pygame
import threading
import os
import time
import moviepy.editor as mpy
from moviepy.video.tools.subtitles import SubtitlesClip

import pysrt
from moviepy.editor import VideoFileClip

speed = 1.0

def timecode_to_seconds(tc):
    return (tc.hours * 3600) + (tc.minutes * 60) + tc.seconds + (tc.milliseconds / 1000.0)

def seconds_to_srt_time(sec):
    hours = int(sec // 3600)
    minutes = int((sec % 3600) // 60)
    seconds = int(sec % 60)
    milliseconds = int((sec - int(sec)) * 1000)
    return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def adjust_subtitles(srt_file, segments, video_path, output_srt_file):
    subs = pysrt.open(srt_file)
    adjusted_subs = pysrt.SubRipFile()
    video = VideoFileClip(video_path)
    fps = video.fps

    for start_frame, end_frame in segments:
        start_time = start_frame / fps
        end_time = end_frame / fps

        for sub in subs:
            sub_start = timecode_to_seconds(sub.start)
            sub_end = timecode_to_seconds(sub.end)

            if sub_start >= start_time and sub_end <= end_time:
                # Adjust subtitle timing
                offset = start_time - sub_start
                sub.start = seconds_to_srt_time(sub_start + offset)
                sub.end = seconds_to_srt_time(sub_end + offset)
                adjusted_subs.append(sub)

    adjusted_subs.save(output_srt_file, encoding='utf-8')

# Function to play audio in a separate thread
def play_audio(audio_path):
    global speed
    freq = int(44100 * speed)  # Standard frequency is 44100 Hz
    pygame.mixer.init(frequency=freq)
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

def get_clip_segment(vidcap, start_frame, duration=10):
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    end_frame = start_frame + int(fps * duration)
    return (start_frame, end_frame)

def save_clip(start_frame, vidcap, output_filename, duration=10):
    frame_count = int(vidcap.get(cv2.CAP_PROP_FPS)) * duration
    current_frame = 0
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, vidcap.get(cv2.CAP_PROP_FPS), (int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    while current_frame < frame_count:
        ret, frame = vidcap.read()
        if ret:
            out.write(frame)
            current_frame += 1
        else:
            break

    out.release()

def create_subtitle_clip(srt_file, video_clip):
    # Generate a subtitle clip
    subtitles = SubtitlesClip(srt_file, lambda txt: mpy.TextClip(txt, font='Arial', fontsize=24, color='white'))
    return subtitles.set_position(('center', 'bottom')).set_duration(video_clip.duration)

def main():
    video_path = '/Users/dhruvildarji/Downloads/17_Again_2009/17Again.mp4'
    audio_path = '/Users/dhruvildarji/Downloads/17_Again_2009/17again.mp3'  # Path to the audio file
    srt_path = '/Users/dhruvildarji/Downloads/17_Again_2009/17Again.srt'  # Path to the SRT file

    vidcap = cv2.VideoCapture(video_path)

    if not vidcap.isOpened():
        print("Error: Could not open video.")
        return
    global speed

    # Start audio in a separate thread
    audio_thread = threading.Thread(target=play_audio, args=(audio_path,)) # 2.0 is audio speed
    audio_thread.start()

    segments = []
    saved_clips = 0

    wait_time = int(1 / (vidcap.get(cv2.CAP_PROP_FPS) * speed) * 1000)

    normal_speed = int(1 / (vidcap.get(cv2.CAP_PROP_FPS) * speed) * 1000)
    fast_forward_speed = normal_speed // 35  # Increase this value for faster speed
    is_fast_forward = False

    while vidcap.isOpened():
        ret, frame = vidcap.read()
        if ret:
            cv2.imshow('Video', frame)
            key = cv2.waitKey(normal_speed if not is_fast_forward else fast_forward_speed) & 0xFF
            if key == ord(' '):
                is_fast_forward = not is_fast_forward
            elif key == ord('s'):
                start_frame = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
                segment = get_clip_segment(vidcap, start_frame)
                segments.append(segment)
                print(f"Segment added: {segment}")
            elif key == ord('q'):
                break

            # if cv2.waitKey(wait_time) & 0xFF == ord('s'):
            #     start_frame = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
            #     segment = get_clip_segment(vidcap, start_frame)
            #     segments.append(segment)
            #     print(f"Segment added: {segment}")
            #     # start_frame = int(vidcap.get(cv2.CAP_PROP_POS_FRAMES))
            #     # save_clip(start_frame, vidcap, f"clip_{saved_clips}.mp4")
            #     # saved_clips += 1
            #     # print(f"Saved clip {saved_clips}")
            # elif cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

        else:
            break

    cv2.destroyAllWindows()

    # Concatenate and save the final video
    if segments:
        print(segments)
        fps = vidcap.get(cv2.CAP_PROP_FPS)

        final_clip = mpy.concatenate_videoclips([mpy.VideoFileClip(video_path).subclip(max(s/fps - 30, 0), min(e/fps, vidcap.get(cv2.CAP_PROP_FRAME_COUNT)/fps)) for s, e in segments])

        final_clip.write_videofile("final_output.mp4")
    output_srt_file = "final_output.srt"
    adjust_subtitles(srt_path, segments, video_path, output_srt_file)

    vidcap.release()

if __name__ == "__main__":
    main()
