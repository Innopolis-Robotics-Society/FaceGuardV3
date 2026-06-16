# Camera = OpenCV
# Detection & Recognition / embeddings = InsightFace
# https://github.com/deepinsight/insightface

import numpy as np  
import cv2
import insightface
from insightface.app import FaceAnalysis

capture = cv2.VideoCapture(0)

face_classifier = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

app = FaceAnalysis('buffalo_l', providers=[
    'CPUExecutionProvider'
])
# buffalo_s for test, better use buffalo_m/l. Customer prefer recognizing, bc is more important than speed

app.prepare(ctx_id=-1,
            det_size=(320,320))
# ctx_id=-1 for CPU, 0 for GPU. (For Pi best option is to use CPU)

def get_face_capture_embedding(capture):
    faces = app.get(capture)
    if len(faces) < 1:
        print("No faces detected in the frame")
    if len(faces) == 1:
        print("One face detected")
    if len(faces) > 1:
        print("Warning: Multiple faces detected. Using first detected face")
    return faces[0].embedding

def get_face_embedding(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    faces = app.get(img)
    
    return faces[0].embedding

def detect_bounding_box(vid):
    gray_image = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    faces = face_classifier.detectMultiScale(gray_image, 1.1, 5, minSize=(60, 60))
    for (x, y, w, h) in faces:
        cv2.rectangle(vid, (x, y), (x + w, y + h), (0, 255, 0), 4)
    return faces    

def compare_faces(captured_face, embedded_face, threshold=0.56):
    cap = np.linalg.norm(captured_face) * np.linalg.norm(embedded_face)
    similarity = np.dot(captured_face, embedded_face) / cap
    return similarity, similarity > threshold

# change this path and choose face image to compare with capture
emb_face = "path/to/face.jpg/png"

while True:
    ret, frame = capture.read()

    frame = cv2.resize(frame, (680, 400))
    faces = detect_bounding_box(
        frame
    ) 

    emb1 = get_face_capture_embedding(frame)
    emb2 = get_face_embedding(emb_face)

    #    print(emb1)

    similarity_score, is_same_person = compare_faces(emb1, emb2)

    print(f"Similarity Score: {similarity_score:.4f}")
    print(f"Same person? {'YES' if is_same_person else 'NO'}")

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) == ord('q'):
        break

capture.release()
cv2.destroyAllWindows()
