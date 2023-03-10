from face_recognition.api import face_locations, face_encodings, compare_faces
import cv2
from pathlib import Path
from argparse import ArgumentParser
from time import time
import numpy as np
from math import *
from threading import Thread, Lock, Event
from alarm import telegram_alert_sync

def locations_and_encodings(img, jitters):
    locs = face_locations(img)
    encs = face_encodings(img, known_face_locations=locs, num_jitters=jitters, model='large')
    return zip(locs, encs)

def detect_edges(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    return edges

def calculate_edge_factor(edges):
    return np.sum(edges) / sqrt(np.shape(edges)[0]*np.shape(edges)[1])

def draw_locs(img, locs, color, width):
    for it in locs:
        cv2.rectangle(
            img,
            (it[3], it[0]),
            (it[1], it[2]),
            color,
            2,
        )

def categorize_face_locations(img, known_encs, jitters, tolerance):
    bad_locs  = []
    good_locs = []

    for loc, enc in locations_and_encodings(img, jitters):
        if any(compare_faces(known_encs, enc, tolerance)):
            good_locs.append(loc)
        else:
            bad_locs.append(loc)

    return bad_locs, good_locs

class Function_Cache():
    def __init__(self, function):
        self.function = function
        self._args = ()
        self._kwargs = {}
        self._lock = Lock()
        self._quit = Event()
        self._thread = Thread(target=self._loop_call)
        self._result = None

    def _loop_call(self):
        while True:
            try:
                with self._lock:
                    args = self._args
                    kwargs = self._kwargs

                result = self.function(*args, **kwargs)

                with self._lock:
                    self._result = result
            except Exception as e:
                print(e)

            if self._quit.is_set():
                break

    def call(self, *args, **kwargs):
        with self._lock:
            self._args = args
            self._kwargs = kwargs
            return self._result

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._quit.set()
        self._thread.join()

def notify(img, msg, evidence_path):
    evidence_path.mkdir(parents=True, exist_ok=True)
    filename = str(evidence_path/f'{floor(time())}-{msg}.jpg')
    cv2.imwrite(filename, img)
    telegram_alert_sync(msg, filename)

def main_loop(
        whitelist,
        evidence_path,
        min_edge_factor,
        camera_id,
        max_risk_time,
        jitters,
        tolerance,
        downscale,
        notification_cooldown,
        debug_info,
    ):
    cap = cv2.VideoCapture(camera_id)

    known_encs = [enc for img in whitelist for loc, enc in locations_and_encodings(img, jitters)]

    prev_frame_ts = time()
    prev_notification_ts = 0
    risk_time = 0

    alarm = False

    with Function_Cache(categorize_face_locations) as fc:
        while True:
            ret, frame = cap.read()

            frame = cv2.resize(frame, (np.shape(frame)[1]//downscale, np.shape(frame)[0]//downscale))

            edges = detect_edges(frame)
            edge_factor = calculate_edge_factor(edges)

            bad_locs, good_locs = fc.call(frame, known_encs=known_encs, jitters=jitters, tolerance=tolerance) or ([], [])

            frame_is_risky = len(bad_locs) > 0 or edge_factor < min_edge_factor

            if frame_is_risky: risk_time += time() - prev_frame_ts
            else             : risk_time -= time() - prev_frame_ts
            prev_frame_ts = time()

            if risk_time > max_risk_time    : alarm = True
            if risk_time < max_risk_time / 2: alarm = False

            risk_time = min(risk_time, max_risk_time)
            risk_time = max(risk_time, 0)

            draw_locs(frame, good_locs, (0, 255, 0), 2)
            draw_locs(frame, bad_locs, (0, 0, 255) if alarm else (0, 255, 255), 2)

            if debug_info:
                print(f'{np.shape(frame)=}')
                print(f'{frame_is_risky=}')
                print(f'{len(bad_locs)=}')
                print(f'{len(good_locs)=}')
                print(f'{edge_factor=}')
                print(f'{risk_time=}')
                print(f'{alarm=}')

            if alarm and time() - prev_notification_ts > notification_cooldown:
                msgs = []
                if len(bad_locs) > 0:             msgs.append(f'{len(bad_locs)} unauthorized faces in view.')
                if edge_factor < min_edge_factor: msgs.append(f'Camera is obstructed.')
                notify(frame, ' '.join(msgs), evidence_path)
                prev_notification_ts = time()

            cv2.imshow('frame', frame)

            if cv2.waitKey(1) == ord('c'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = ArgumentParser(description='Detect and match faces to whitelist')
    parser.add_argument('--whitelist', type=Path, help='Directory with whitelisted people. Default: whitelist', default=Path('whitelist/'))
    parser.add_argument('--evidence', type=Path, help='Directory where to save the evidence', default=Path('evidence/'))
    parser.add_argument('--jitters', type=int, help='Number of jitters for face', default=1)
    parser.add_argument('--tolerance', type=float, help='Tolerance for maching faces', default=0.6)
    parser.add_argument('--camera-id', type=int, help='Id of camera to use for video', default=0)
    parser.add_argument('--max-risk-time', type=float, help='Seconds of an unsecure conditions before raising the alarm', default=1.0)
    parser.add_argument('--min-edge-factor', type=float, help='Treshold for declaring the camera obstructed', default=1000)
    parser.add_argument('--downscale', type=int, help='Downscaling of camera input', default=1)
    parser.add_argument('--notification-cooldown', type=int, help='Minimum seconds between notifications', default=60)
    parser.add_argument('--debug-info', action='store_true', help='Show debug info', default=False)

    args = parser.parse_args()

    try:
        whitelist = [cv2.imread(str(it)) for it in Path(args.whitelist).iterdir()]
    except:
        whitelist = []

    main_loop(
        whitelist=whitelist,
        evidence_path=args.evidence,
        max_risk_time=args.max_risk_time,
        jitters=args.jitters,
        tolerance=args.tolerance,
        camera_id=args.camera_id,
        min_edge_factor=args.min_edge_factor,
        downscale=args.downscale,
        notification_cooldown=args.notification_cooldown,
        debug_info=args.debug_info,
    )
