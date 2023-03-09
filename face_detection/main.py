from face_recognition.api import face_locations, face_encodings, compare_faces
import cv2
from pathlib import Path
from argparse import ArgumentParser

def locations_and_encodings(img, jitters):
    locs = face_locations(img)
    encs = face_encodings(img, known_face_locations=locs, num_jitters=jitters, model='large')
    return zip(locs, encs)

def face_detect(camera_id, whitelist, jitters, tolerance):
    cap = cv2.VideoCapture(camera_id)

    known_encs = [enc for img in whitelist for loc, enc in locations_and_encodings(img, jitters)]

    while True:
        # Read a frame from the camera
        ret, frame = cap.read()

        for loc, enc in locations_and_encodings(frame, jitters):
            if any(compare_faces(known_encs, enc, tolerance)):
                col = (0, 255, 0)
            else:
                col = (0, 0, 255)

            cv2.rectangle(
                frame,
                (loc[3], loc[0]),
                (loc[1], loc[2]),
                col,
                2,
            )

        # Display the frame in a window
        cv2.imshow('frame', frame)

        # Wait for a key press and exit if the 'q' key is pressed
        if cv2.waitKey(1) == ord('c'):
            break


    # Release the capture and destroy the window
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = ArgumentParser(description='Detect and match faces to whitelist')
    parser.add_argument('--whitelist', type=Path, help='Directory with whitelisted people. Default: whitelist', default=Path('whitelist/'))
    parser.add_argument('--jitters', type=int, help='Number of jitters for face', default=1)
    parser.add_argument('--tolerance', type=float, help='Tolerance for maching faces', default=0.6)
    parser.add_argument('--camera-id', type=int, help='Id of camera to use for video', default=0)

    args = parser.parse_args()

    try:
        whitelist = [cv2.imread(str(it)) for it in Path(args.whitelist).iterdir()]
    except:
        whitelist = []

    face_detect(args.camera_id, whitelist, args.jitters, args.tolerance)
