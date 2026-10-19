from unittest.mock import patch

from aicconnector import aicconnector
from aicconnector.aicconnector import AicConnector
from aicconnector.config import AicConnectorConfig, HttpOutputConfig, MinioConfig, RedisInputConfig
from visionapi.sae_pb2 import SaeMessage


def make_connector():
    minio = MinioConfig(
        endpoint="minio:9000",
        user="user",
        password="pass",
        bucket_name="bucket",
        secure=False,
    )
    http_output = HttpOutputConfig(
        target_endpoint="http://target",
        module_name="mod",
        minio=minio,
    )
    redis_input = RedisInputConfig(
        stream_ids=["stream1"],
        stream_prefix="objectdetector",
    )
    config = AicConnectorConfig(redis_input=redis_input, http_output=http_output)
    return AicConnector(config), minio


def test_main_module_import():
    assert hasattr(aicconnector, "AicConnector") or hasattr(aicconnector, "main")


def test_save_sae_message_unchanged():
    connector, minio = make_connector()
    msg = SaeMessage()
    msg.detections.add().class_id = 2
    msg.model_metadata.class_names[2] = "detector-class"
    msg.sampling_metadata.add().filter_matches.add().name = "example-filter"
    sae_bytes = msg.SerializeToString()

    with patch("aicconnector.aicconnector.save_file_to_minio") as save_file_to_minio:
        connector._save_sae_message(sae_bytes, "sae-id")

    upload = save_file_to_minio.call_args
    assert upload.args[0] == minio
    assert upload.args[1] == sae_bytes
    assert upload.args[2] == "sae-id/sae.pb"
    assert upload.kwargs["content_type"] == "application/x-protobuf"
