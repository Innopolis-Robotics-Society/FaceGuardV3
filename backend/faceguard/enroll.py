import cv2

from .detect import draw_face_box
from .recognize import (
    create_face_app,
    extract_embedding_from_frame,
    average_embeddings,
    save_embedding,
    LivenessDetector,
)


def enroll_user(
    embedding_path: str = "data/user_embedding.npy",
    target_count: int = 50,
    camera_index: int = 0,
):
    app = create_face_app()
    liveness_detector = LivenessDetector()

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    embeddings = []

    while len(embeddings) < target_count:
        ret, frame = cap.read()

        if not ret:
            break

        embedding, face, status = extract_embedding_from_frame(app, liveness_detector, frame)

        if status == "real" and embedding is not None and face is not None:
            embeddings.append(embedding)

            draw_face_box(
                frame,
                face,
                f"Collecting: {len(embeddings)}/{target_count}",
                color=(0, 255, 0),
            )
        elif status == "spoof":
            draw_face_box(frame, face, "SPOOFING ATTEMPT", color = (0, 0, 255))
        elif status == "bad_face":
            draw_face_box(frame, face, "Bad angle/blur", color = (0, 255, 255))
        else:
            cv2.putText(
                frame,
                "Show your face to the camera",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

        cv2.putText(
            frame,
            "Enrollment mode | Press ESC to stop",
            (30, frame.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Enrollment", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    if len(embeddings) < 10:
        raise RuntimeError(
            f"Not enough embeddings collected: {len(embeddings)}. Need at least 10"
        )

    mean_embedding = average_embeddings(embeddings)

    save_embedding(embedding_path, mean_embedding)

    print("Enrollment finished.")
    print(f"Collected embeddings: {len(embeddings)}")
    print(f"Saved to: {embedding_path}")