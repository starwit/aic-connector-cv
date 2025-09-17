import json
import logging
import subprocess
import time
import zipfile
from pathlib import Path
from zlib import crc32

import cv2
import numpy as np
from minio import Minio
from visionapi.sae_pb2 import Detection

from .config import MinioConfig

log = logging.getLogger(__name__)

def save_file_to_minio(minio_config: MinioConfig, file_path: str, object_name: str) -> None:
    client = Minio(
        endpoint=minio_config.endpoint,
        access_key=minio_config.user,
        secret_key=minio_config.password,
        secure=minio_config.secure
    )

    # Determine content type based on file extension
    content_type = {
        '.zip': 'application/zip',
        '.jpg': 'image/jpeg',
        '.json': 'application/json',
    }.get(Path(file_path).suffix, 'application/octet-stream')

    try:
        client.fput_object(
            minio_config.bucket_name,
            object_name, 
            file_path=file_path,
            content_type=content_type
        )
    except Exception as e:
        raise IOError(f"Could not upload file {file_path} to MinIO") from e

def draw_bonding_boxes_in_frame(frame, detections: list[Detection]) -> bytes:
    center_points = []

    for det in detections:
        if det.timestamp_utc_ms == frame.timestamp_utc_ms:
            center_points.append(det.bounding_box.min_x)

    frame_data = frame.frame_data_jpeg
    np_arr = np.frombuffer(frame_data, np.uint8)
    frame_img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

    height, width = frame_img.shape[:2]

    for point in center_points:
        x, y = point.x, point.y
        x = int(x * width)
        y = int(y * height)
        cv2.circle(frame_img, (x, y), 20, (0, 0, 255), -1)

    _, encoded_img = cv2.imencode('.jpeg', frame_img)
    if isinstance(encoded_img, bytes):
        return encoded_img
    else:   
        return encoded_img.tobytes()

