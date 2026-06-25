import argparse
import cv2

from .enroll import enroll_user
from .recognize import (
    create_face_app,
    extract_embedding_from_frame,
    load_embedding,
    verify_embedding,
    LivenessDetector,
)
from .detect import draw_face_box


def run_recognition(
    embedding_path: str = "data/user_embedding.npy",
    threshold: float = 0.50,
    camera_index: int = 0,
):
    app = create_face_app()
    liveness_detector = LivenessDetector()
    saved_embedding = load_embedding(embedding_path)

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError("Cannot open camera.")

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        current_embedding, face, status = extract_embedding_from_frame(app, liveness_detector, frame)

        if status == "real" and current_embedding is not None and face is not None:
            verified, score = verify_embedding(
                current_embedding=current_embedding,
                saved_embedding=saved_embedding,
                threshold=threshold,
            )

            if verified:
                label = f"ACCESS GRANTED | score={score:.3f}"
                color = (0, 255, 0)
            else:
                label = f"ACCESS DENIED | score={score:.3f}"
                color = (0, 0, 255)

            draw_face_box(frame, face, label, color=color)
        
        elif status == "spoof":
            draw_face_box(frame, face, "ACCESS DENIED: SPOOF", color = (0, 0, 255))
        
        elif status == "bad_face":
            draw_face_box(frame, face, "Look straight", color = (0, 255, 255))

        else:
            cv2.putText(
                frame,
                "No valid face detected",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 0, 0), #было (0, 0, 255)
                2,
            )

        cv2.putText(
            frame,
            "Recognition mode | Press ESC to stop",
            (30, frame.shape[0] - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        cv2.imshow("Recognition", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="FaceGuard MVP")

    parser.add_argument(
        "mode",
        choices=["enroll", "recognize"],
        help="Run enrollment or recognition mode.",
    )

    parser.add_argument(
        "--embedding-path",
        default="data/user_embedding.npy",
        help="Path to saved user embedding.",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Cosine similarity threshold.",
    )

    parser.add_argument(
        "--target-count",
        type=int,
        default=50,
        help="Number of embeddings to collect during enrollment.",
    )

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Camera index for OpenCV VideoCapture.",
    )

    args = parser.parse_args()

    if args.mode == "enroll":
        enroll_user(
            embedding_path=args.embedding_path,
            target_count=args.target_count,
            camera_index=args.camera_index,
        )

    elif args.mode == "recognize":
        run_recognition(
            embedding_path=args.embedding_path,
            threshold=args.threshold,
            camera_index=args.camera_index,
        )


if __name__ == "__main__":
    main()