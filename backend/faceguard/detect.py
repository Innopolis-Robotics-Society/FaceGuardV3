def get_bbox_area(face) -> float:
    x1, y1, x2, y2 = face.bbox
    return float((x2 - x1) * (y2 - y1))


def select_closest_face(faces):
    if faces is None or len(faces) == 0:
        return None

    return max(faces, key=get_bbox_area)


def clamp_bbox(bbox, frame_shape, padding: int = 0):
    #frame.shape = (height, width, channels)
    frame_h, frame_w = frame_shape[:2]

    x1, y1, x2, y2 = bbox.astype(int)

    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(frame_w, x2 + padding)
    y2 = min(frame_h, y2 + padding)

    return x1, y1, x2, y2


def crop_face(frame, face, padding: int = 40):
    # Crop selected face fromm frame
    if face is None:
        return None

    x1, y1, x2, y2 = clamp_bbox(face.bbox, frame.shape, padding)

    if x2 <= x1 or y2 <= y1:
        return None

    return frame[y1:y2, x1:x2]


def is_good_face(
    face,
    frame,
    min_size: int = 90,
    min_det_score: float = 0.70,
) -> bool:
    if face is None:
        return False

    x1, y1, x2, y2 = clamp_bbox(face.bbox, frame.shape, padding=0)

    face_w = x2 - x1
    face_h = y2 - y1

    if face_w < min_size or face_h < min_size:
        return False

    det_score = getattr(face, "det_score", None)

    if det_score is not None and det_score < min_det_score:
        return False

    raw_embedding = getattr(face, "embedding", None)
    normed_embedding = getattr(face, "normed_embedding", None)

    if raw_embedding is None and normed_embedding is None:
        return False

    return True


def draw_face_box(frame, face, text: str, color=(0, 255, 0)):
    import cv2

    if face is None:
        return frame

    x1, y1, x2, y2 = clamp_bbox(face.bbox, frame.shape, padding=0)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    cv2.putText(
        frame,
        text,
        (x1, max(30, y1 - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
    )

    return frame
