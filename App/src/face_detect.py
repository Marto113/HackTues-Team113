from face_recognition.api import face_encodings, compare_faces
import cv2
from pathlib import Path
from argparse import ArgumentParser
from time import time, sleep
import numpy as np
from math import *
from threading import Thread, Lock, Event, get_ident as get_thread_ident
from serial import Serial

nets = {}

def face_locations(img):
    net = nets.setdefault(get_thread_ident(), cv2.dnn.readNetFromCaffe('deploy.prototxt.txt', 'res10_300x300_ssd_iter_140000.caffemodel'))

    (h, w) = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    nets[get_thread_ident()].setInput(blob)
    detections = nets[get_thread_ident()].forward()

    locs = []

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > .75:
            locs.append((
                floor(detections[0, 0, i, 4] * h),
                floor(detections[0, 0, i, 5] * w),
                floor(detections[0, 0, i, 6] * h),
                floor(detections[0, 0, i, 3] * w),
            ))

    return locs

def notify(img, msg, evidence_path):
    print('Sending notification:', msg)
    evidence_path.mkdir(parents=True, exist_ok=True)
    filename = str(evidence_path/f'{floor(time())}-{msg}.jpg')
    cv2.imwrite(filename, img)

def locations_and_encodings(img, jitters):
    locs = face_locations(img)
    encs = face_encodings(img, known_face_locations=locs, num_jitters=jitters, model='large')
    return zip(locs, encs)

def calculate_edge_factor(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    return np.sum(edges) / sqrt(edges.shape[0]*edges.shape[1])

def draw_locs(img, locs, color, width):
    ret = img.copy()
    for it in locs:
        cv2.rectangle(
            ret,
            (it[3], it[0]),
            (it[1], it[2]),
            color,
            2,
        )
    return ret

def categorize_face_locations(img, known_encs, jitters, tolerance):
    bad_locs  = []
    good_locs = []

    for loc, enc in locations_and_encodings(img, jitters):
        if any(compare_faces(known_encs, enc, tolerance)):
            good_locs.append(loc)
        else:
            bad_locs.append(loc)

    return bad_locs, good_locs, calculate_edge_factor(img), img

class Function_Cache():
    def __init__(self, function):
        self.function = function
        self._args = ()
        self._kwargs = {}
        self._lock = Lock()
        self._quit = Event()
        self._thread = Thread(target=self._loop_call)
        self._result = None
        self._score = 0

    def _loop_call(self):
        while True:
            try:
                with self._lock:
                    args = self._args
                    kwargs = self._kwargs

                result = self.function(*args, **kwargs)

                with self._lock:
                    self._result = result
                    self._score = 0
            except Exception as e:
                pass

            if self._quit.is_set():
                break

    def call(self, score, *args, **kwargs):
        with self._lock:
            if score > self._score:
                self._score = score
                self._args = args
                self._kwargs = kwargs
            return self._result

    def invalidate(self):
        with self._lock:
            self._result = None
            self._score = 0

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
            with self._lock:
                self._quit.set()
            self._thread.join()

def try_iterdir(path):
    try:
        return [str(it) for it in sorted(path.iterdir())]
    except:
        return []

def rescan_whitelist(whitelist_path, filenames, known_encs, jitters):
    cur_filenames = try_iterdir(whitelist_path)

    if filenames == cur_filenames:
        return filenames, known_encs, False

    print('Whitelist change detected. Rescanning...')
    cur_known_encs = []
    for name in cur_filenames:
        print(name)
        img = cv2.imread(name)
        for loc, enc in locations_and_encodings(img, jitters):
            cur_known_encs.append(enc)
    print('Whitelist rescanned!')
    return cur_filenames, cur_known_encs, True

def main_loop(
        whitelist_path,
        evidence_path,
        min_edge_factor,
        camera_id,
        max_risk_time,
        jitters,
        tolerance,
        downscale,
        action_cooldown,
        debug_info,
        serial_port,
    ):
    cap = cv2.VideoCapture(camera_id)

    prev_frame_ts = time()
    prev_action_ts = 0
    risk_time = 0

    serial = Serial(serial_port, 9600)

    alarm = False

    filenames = []
    known_encs = []

    do_face_detect = False;

    with Function_Cache(categorize_face_locations) as fc:
        while True:
            filenames, known_encs, changed = rescan_whitelist(whitelist_path, filenames, known_encs, jitters)
            if changed:
                prev_frame_ts = time()

            ret, frame = cap.read()

            frame = np.rot90(frame, 2)

            if not ret:
                print('Error getting frames from camera')
                break

            frame = cv2.resize(frame, (floor(frame.shape[1]/downscale), floor(frame.shape[0]/downscale)))

            while serial.in_waiting:
                cmd = serial.read().decode('utf-8')
                if cmd == 'a':
                    do_face_detect = True
                if cmd == 'm':
                    do_face_detect = False

            if do_face_detect:
                result = fc.call(calculate_edge_factor(frame), frame, known_encs=known_encs, jitters=jitters, tolerance=tolerance)
            else:
                result = [], [], calculate_edge_factor(frame), frame

            if result is None:
                prev_frame_ts = time()
                continue

            bad_locs, good_locs, locs_edge_factor, locs_frame = result

            bad_centers = [(it[1]+it[3]) / 2 / frame.shape[1] - 0.5 for it in bad_locs]

            frame_is_risky = len(bad_locs) > 0 or locs_edge_factor < min_edge_factor

            if frame_is_risky: risk_time += time() - prev_frame_ts
            else             : risk_time -= time() - prev_frame_ts
            prev_frame_ts = time()

            if risk_time > max_risk_time    : alarm = True
            if risk_time < max_risk_time / 2: alarm = False

            risk_time = min(risk_time, max_risk_time)
            risk_time = max(risk_time, 0)

            if alarm and bad_centers and time() - prev_action_ts > action_cooldown:
                msgs = []
                if len(bad_locs) > 0:                  msgs.append(f'{len(bad_locs)} unauthorized faces in view.')
                if locs_edge_factor < min_edge_factor: msgs.append(f'Camera is obstructed.')

                if len(msgs) != 0:
                    locs_frame = draw_locs(locs_frame, good_locs, (0, 255, 0), 2)
                    locs_frame = draw_locs(locs_frame, bad_locs, (0, 0, 255), 2)

                    prev_notification_ts = time()
                    notify(locs_frame, ' '.join(msgs), evidence_path)

                prev_action_ts = time()
                closest_center = sorted(bad_centers, key=lambda x: abs(x))[0]
                delta = round(-45 * closest_center + 45)
                delta_bytes = delta.to_bytes(1, 'big', signed=True)
                serial.write(
                    'r'.encode('utf-8') +
                    delta.to_bytes(1, 'big', signed=True) +
                    't'.encode('utf-8')
                )
                fc.invalidate()


            if debug_info:
                frame = draw_locs(frame, good_locs, (0, 255, 0), 2)
                frame = draw_locs(frame, bad_locs, (0, 0, 255) if alarm else (0, 255, 255), 2)

                cv2.imshow('frame', frame)
                if cv2.waitKey(1) == ord('c'):
                    break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = ArgumentParser(description='Detect and match faces to whitelist')
    parser.add_argument('--whitelist', type=Path, help='Directory with whitelisted people. Default: whitelist', default=Path('../whitelist/'))
    parser.add_argument('--evidence', type=Path, help='Directory where to save the evidence', default=Path('../evidence/'))
    parser.add_argument('--jitters', type=int, help='Number of jitters for face encoding', default=1)
    parser.add_argument('--tolerance', type=float, help='Tolerance for maching faces', default=0.6)
    parser.add_argument('--camera-id', type=int, help='Id of camera to use for video', default=1)
    parser.add_argument('--max-risk-time', type=float, help='Seconds of an unsecure conditions before raising the alarm', default=1)
    parser.add_argument('--min-edge-factor', type=float, help='Treshold for declaring the camera obstructed', default=1500)
    parser.add_argument('--downscale', type=float, help='Downscaling of camera input', default=1)
    parser.add_argument('--action-cooldown', type=float, help='Minimum seconds between reactions', default=3)
    parser.add_argument('--debug-info', action='store_true', help='Show debug info', default=False)
    parser.add_argument('--serial-port', type=str, help='The serial port', default='COM9')

    args = parser.parse_args()

    main_loop(
        whitelist_path=args.whitelist,
        evidence_path=args.evidence,
        max_risk_time=args.max_risk_time,
        jitters=args.jitters,
        tolerance=args.tolerance,
        camera_id=args.camera_id,
        min_edge_factor=args.min_edge_factor,
        downscale=args.downscale,
        action_cooldown=args.action_cooldown,
        debug_info=args.debug_info,
        serial_port=args.serial_port,
    )
