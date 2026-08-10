import json
from unittest.mock import patch

import pytest

from aicconnector import aicconnector
from aicconnector.aicconnector import AicConnector
from aicconnector.config import AicConnectorConfig, HttpOutputConfig, MinioConfig, RedisInputConfig
from visionapi.sae_pb2 import SaeMessage


def test_main_module_import():
    assert hasattr(aicconnector, "AicConnector") or hasattr(aicconnector, "main")


def test_save_sae_detections_as_json():
    minio = MinioConfig(endpoint="minio:9000", user="user", password="pass", bucket_name="bucket", secure=False)
    http_output = HttpOutputConfig(target_endpoint="http://target", module_name="mod", minio=minio)
    redis_input = RedisInputConfig(stream_ids=["stream1"], stream_prefix="objectdetector")
    connector = AicConnector(AicConnectorConfig(redis_input=redis_input, http_output=http_output))
    msg = SaeMessage()
    detection = msg.detections.add()
    detection.class_id = 2
    detection.bounding_box.min_x = 0.125
    detection.bounding_box.min_y = 0.25
    detection.bounding_box.max_x = 0.5
    detection.bounding_box.max_y = 0.75
    msg.model_metadata.class_names[2] = "detector-class"

    with patch("aicconnector.aicconnector.save_file_to_minio") as save_file_to_minio:
        connector._save_sae_detections(msg, "sae-id")

    upload = save_file_to_minio.call_args
    assert upload.args[0] == minio
    assert upload.args[2] == "sae-id/detections.json"
    assert upload.kwargs["content_type"] == "application/json"
    assert json.loads(upload.args[1]) == [{
        "label": "detector-class",
        "boundingBox": {"minX": 0.125, "minY": 0.25, "maxX": 0.5, "maxY": 0.75},
    }]


def test_rejects_partial_decision_type_mapping():
    with pytest.raises(ValueError, match="Missing decision type names for streams: stream2"):
        RedisInputConfig(
            stream_ids=["stream1", "stream2"],
            stream_prefix="objectdetector",
            decision_type_names={"stream1": "Periodic sample"},
        )


def test_does_not_send_decision_after_file_upload_failure():
    minio = MinioConfig(endpoint="minio:9000", user="user", password="pass", bucket_name="bucket", secure=False)
    http_output = HttpOutputConfig(target_endpoint="http://target", module_name="mod", minio=minio)
    redis_input = RedisInputConfig(stream_ids=["stream1"], stream_prefix="objectdetector")
    connector = AicConnector(AicConnectorConfig(redis_input=redis_input, http_output=http_output))
    msg = SaeMessage()

    with (
        patch.object(connector, "_save_sae_media"),
        patch.object(connector, "_save_annotated_sae_media", side_effect=IOError),
        patch.object(connector.http_output, "send_decision_message") as send_decision_message,
    ):
        connector.get(msg.SerializeToString())

    send_decision_message.assert_not_called()
