import cv2 as cv
import numpy as np
import signal
import os
import time

WD = os.getcwd()

resolution = 500, 400
fps = 60
video_root = f'{WD}/static/live'
playlist_root = 'http://127.0.0.1:8080/live'

# caps = f' ! video/x-raw,width={resolution[0]},height={resolution[1]},framerate={fps}/1,format=RGB'
# caps = ''

encoder = f'x264enc speed-preset=ultrafast '
pipeline = f'appsrc is-live=true ! videoconvert ! video/x-raw,format=I420 ! {encoder} ! mpegtsmux ! hlssink target-duration=5 max-files=15 ' \
           f'playlist-root={playlist_root} ' \
           f'location={video_root}/video_%05d.ts ' \
           f'playlist-location={video_root}/playlist.m3u8'

signal.signal(signal.SIGPIPE, signal.SIG_DFL)
os.environ['GST_DEBUG'] = "*:1"
out = cv.VideoWriter(
    pipeline,
    cv.CAP_GSTREAMER,
    0, fps, resolution
)
out.set(cv.CAP_PROP_FORMAT, cv.CAP_PROP_CONVERT_RGB)
if not out.isOpened():
    raise RuntimeError("Could not open gstreamer output")

frame = np.zeros(resolution + (3,), dtype='uint8')
frame[:, :, 0] = 255
n = 0
try:
    while True:
        if n % 100 == 0:
            print(f'frame =', n)
        n += 1
        frame[:, :, 2] += 1
        frame[:, :, 2] %= 256
        frame[100:200, 100:200, :] = np.random.randint(0, 255, 3 * 100 * 100).reshape(100, 100, 3)
        out.write(frame)
        time.sleep(1 / fps)
finally:
    out.release()
    os.system('bash -c "find \'static/live\' -type f | grep -v .keep | xargs rm -f"')
