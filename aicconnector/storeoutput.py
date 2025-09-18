import logging
import sys

import cv2
import numpy as np
from minio import Minio
from visionapi.sae_pb2 import Detection, SaeMessage

from .config import MinioConfig
from io import BytesIO
from turbojpeg import TurboJPEG

jpeg = TurboJPEG()

ANNOTATION_COLOR = (0, 0, 255)
DEFAULT_WINDOW_SIZE = (1280, 720)

log = logging.getLogger(__name__)

def save_file_to_minio(minio_config: MinioConfig, data: bytes, object_name: str) -> None:
    client = Minio(
        endpoint=minio_config.endpoint,
        access_key=minio_config.user,
        secret_key=minio_config.password,
        secure=minio_config.secure
    )

    try:
        client.put_object(
            minio_config.bucket_name,
            object_name, 
            data=BytesIO(data),
            length=len(data),
            content_type="image/jpeg"
        )
    except Exception as e:
        raise IOError(f"Could not upload file {object_name} to MinIO") from e

def draw_bonding_boxes_in_frame(sae_msg: SaeMessage) -> bytes:
    frame_data = sae_msg.frame.frame_data_jpeg
    np_arr = np.frombuffer(frame_data, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)

    for detection in sae_msg.detections:
        _annotate(image, detection)
    
    _, encoded_img = cv2.imencode('.jpeg', image)
    return encoded_img.tobytes()

def _annotate(image, detection: Detection):
    bbox_x1 = int(detection.bounding_box.min_x * image.shape[1])
    bbox_y1 = int(detection.bounding_box.min_y * image.shape[0])
    bbox_x2 = int(detection.bounding_box.max_x * image.shape[1])
    bbox_y2 = int(detection.bounding_box.max_y * image.shape[0])

    class_id = detection.class_id
    conf = detection.confidence

    label = f'{class_id} - {round(conf,2)}'

    if detection.object_id is not None:
        object_id = detection.object_id.hex()[:4]
        label = f'ID {object_id} - {class_id} - {round(conf,2)}'

    line_width = max(round(sum(image.shape) / 2 * 0.002), 2)

    cv2.rectangle(image, (bbox_x1, bbox_y1), (bbox_x2, bbox_y2), color=ANNOTATION_COLOR, thickness=line_width, lineType=cv2.LINE_AA)
    cv2.putText(image, label, (bbox_x1, bbox_y1 - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX, color=ANNOTATION_COLOR, thickness=round(line_width/3), fontScale=line_width/4, lineType=cv2.LINE_AA)
    return image   
