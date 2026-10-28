import base64
import json
import os

import cv2
import numpy as np
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


MODEL_VERSION = "opencv-sface-2021dec"
FACE_DETECTOR_PATH = "/home/ubuntu/hrms-private/face-models/face_detection_yunet_2023mar.onnx"
FACE_RECOGNIZER_PATH = "/home/ubuntu/hrms-private/face-models/face_recognition_sface_2021dec.onnx"

# OpenCV models are loaded lazily to avoid using RAM on unrelated requests.
_detector = None
_recognizer = None


class FaceServiceError(Exception):
    pass


def _cipher():
    key = os.environ.get("FACE_ENCRYPTION_KEY", "").strip()
    if not key:
        raise FaceServiceError("Face encryption key is not configured.")

    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise FaceServiceError("Face encryption key is invalid.") from exc


def _models():
    global _detector, _recognizer

    if _detector is None:
        if not os.path.isfile(FACE_DETECTOR_PATH):
            raise FaceServiceError("Face detection model is missing.")
        _detector = cv2.FaceDetectorYN.create(
            FACE_DETECTOR_PATH, "", (320, 320),
            score_threshold=0.85,
            nms_threshold=0.3,
            top_k=5000,
        )

    if _recognizer is None:
        if not os.path.isfile(FACE_RECOGNIZER_PATH):
            raise FaceServiceError("Face recognition model is missing.")
        _recognizer = cv2.FaceRecognizerSF.create(
            FACE_RECOGNIZER_PATH, ""
        )

    return _detector, _recognizer


def _decode_image(image_bytes):
    if not image_bytes or len(image_bytes) > 5 * 1024 * 1024:
        raise FaceServiceError("Image must be between 1 byte and 5 MB.")

    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if image is None or image.size == 0:
        raise FaceServiceError("The uploaded image is not a valid image.")

    height, width = image.shape[:2]
    if width < 160 or height < 160 or width > 4096 or height > 4096:
        raise FaceServiceError("Image dimensions are not supported.")

    return image


def extract_embedding(image_bytes):
    """Return a normalized SFace embedding; never save the input image."""
    image = _decode_image(image_bytes)
    detector, recognizer = _models()
    height, width = image.shape[:2]
    detector.setInputSize((width, height))

    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        raise FaceServiceError("No face detected. Keep your face clearly visible.")
    if len(faces) != 1:
        raise FaceServiceError("Only one face should be visible in the image.")

    aligned = recognizer.alignCrop(image, faces[0])
    feature = recognizer.feature(aligned).reshape(-1).astype(np.float32)

    norm = float(np.linalg.norm(feature))
    if not np.isfinite(norm) or norm == 0:
        raise FaceServiceError("Could not process this face. Please try again.")

    feature /= norm
    return feature


def encrypt_embedding(embedding):
    array = np.asarray(embedding, dtype=np.float32).reshape(-1)
    if array.size != 128 or not np.all(np.isfinite(array)):
        raise FaceServiceError("Face template has an invalid format.")

    payload = json.dumps({
        "version": MODEL_VERSION,
        "embedding": base64.b64encode(array.tobytes()).decode("ascii"),
    }).encode("utf-8")

    return _cipher().encrypt(payload)


def decrypt_embedding(encrypted_template):
    try:
        payload = json.loads(_cipher().decrypt(bytes(encrypted_template)))
        if payload.get("version") != MODEL_VERSION:
            raise FaceServiceError("Face template model version does not match.")

        vector = np.frombuffer(
            base64.b64decode(payload["embedding"], validate=True),
            dtype=np.float32,
        ).copy()

        if vector.size != 128 or not np.all(np.isfinite(vector)):
            raise FaceServiceError("Stored face template is invalid.")

        return vector
    except InvalidToken as exc:
        raise FaceServiceError("Unable to decrypt the stored face template.") from exc
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise FaceServiceError("Stored face template is invalid.") from exc


def compare_embeddings(first, second):
    """Cosine similarity; threshold must be calibrated on real test data."""
    a = np.asarray(first, dtype=np.float32).reshape(-1)
    b = np.asarray(second, dtype=np.float32).reshape(-1)
    if a.size != 128 or b.size != 128:
        raise FaceServiceError("Face template dimensions are invalid.")

    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0 or not np.isfinite(denominator):
        raise FaceServiceError("Could not compare the face templates.")

    return float(np.dot(a, b) / denominator)
