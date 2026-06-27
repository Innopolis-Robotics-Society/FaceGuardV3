from .enroll import enroll_user


def collect_user_face_dataset(
    embedding_path: str = "data/user_embedding.npy",
    target_count: int = 50,
    camera_index: int = 0,
):
    return enroll_user(
        embedding_path=embedding_path,
        target_count=target_count,
        camera_index=camera_index,
    )
