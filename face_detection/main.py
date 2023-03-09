from face_recognition.api import face_locations, face_encodings, compare_faces
import cv2
from pathlib import Path

from argparse import ArgumentParser

def locations_and_encodings(img, gpu=False):
    locs = face_locations(
        img,
        number_of_times_to_upsample = 4 if gpu else 1,
        model = 'cnn' if gpu else 'hog',
    )
    encs = face_encodings(
        img,
        known_face_locations=locs,
        num_jitters = 4 if gpu else 1,
        model = 'large',
    )

    return locs, encs

# Open the default camera (usually 0)
def face_detect(whitelist, gpu=False):
    cap = cv2.VideoCapture(0)


    known_encs = [enc for img in whitelist for enc in locations_and_encodings(img)[1]]

    while True:
        # Read a frame from the camera
        ret, frame = cap.read()

        locations, encodings = locations_and_encodings(frame, gpu)
        for loc, enc in zip(locations, encodings):

            if any(compare_faces(known_encs, enc)):
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
    parser.add_argument('--gpu', action='store_true', help='Use high performance settings', default=False)
    parser.add_argument('--whitelist', type=Path, help='Directory with whitelisted people. Default: whitelist', default=Path('whitelist/'))

    args = parser.parse_args()

    try:
        whitelist = [cv2.imread(str(it)) for it in Path(args.whitelist).iterdir()]
    except:
        whitelist = []

    face_detect(whitelist, args.gpu)
