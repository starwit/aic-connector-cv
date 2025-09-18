import logging
import os
from pathlib import Path
from typing import Any
from datetime import datetime
from prometheus_client import Counter, Histogram, Summary
from visionapi.sae_pb2 import SaeMessage
from uuid import uuid4
from .config import AicConnectorConfig
from .httpoutput import HttpOutput
from aicconnector.storeoutput import (save_file_to_minio)


logging.basicConfig(format='%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s')
logger = logging.getLogger(__name__)

GET_DURATION = Histogram('aic_connector_get_duration', 'The time it takes to deserialize the proto until returning the tranformed result as a serialized proto',
                         buckets=(0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25))
OBJECT_COUNTER = Counter('aic_connector_object_counter', 'How many detections have been transformed')
PROTO_SERIALIZATION_DURATION = Summary('aic_connector_proto_serialization_duration', 'The time it takes to create a serialized output proto')
PROTO_DESERIALIZATION_DURATION = Summary('aic_connector_proto_deserialization_duration', 'The time it takes to deserialize an input proto')


class AicConnector:
    def __init__(self, config: AicConnectorConfig) -> None:
        self.config = config
        self.http_output = HttpOutput(config.http_output, config.log_level) if config.http_output else None
        self.isDebug = self.config.log_level.value == 'DEBUG'
        logger.setLevel(self.config.log_level.value)

    def __call__(self, input_proto) -> Any:
        return self.get(input_proto)
    
    @GET_DURATION.time()
    def get(self, input_proto):
        sae_msg: SaeMessage = self._unpack_proto(input_proto)
        sae_id = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{uuid4().hex[:6]}'
        self._save_sae_media(sae_msg, sae_id)
        if self.http_output:
            self.http_output.send_decision_message(sae_msg, sae_id)
        
    @PROTO_DESERIALIZATION_DURATION.time()
    def _unpack_proto(self, sae_message_bytes):
        sae_msg = SaeMessage()
        sae_msg.ParseFromString(sae_message_bytes)

        return sae_msg
    
    @PROTO_SERIALIZATION_DURATION.time()
    def _pack_proto(self, sae_msg: SaeMessage):
        return sae_msg.SerializeToString()

    def _save_sae_media(self, input_msg: SaeMessage, sae_id: str):
        frame = input_msg.frame.frame_data_jpeg

        try:
            # Create a temporary directory and store all necessary output artifacts
            temp_output_dir = Path('./output')
            os.makedirs(temp_output_dir, exist_ok=True)
            #store_annotated_frame(temp_output_dir / 'annotated.jpg', frame, trajectories)

            # Copy output artifacts to local storage
            #if self.config.local_output is not None:
            #    shutil.copytree(temp_output_dir, self.config.local_output.path / sae_id, dirs_exist_ok=True)
            
            # Upload output artifacts to MinIO if http_output is configured
            if self.config.http_output is not None:
                for file in temp_output_dir.iterdir():
                    object_name = f"{sae_id}/{file.name}"
                    save_file_to_minio(self.config.http_output.minio, file, object_name)
        except Exception as e:
            logger.error(f"Error saving decisions: {e}")

        # Clean up
        # shutil.rmtree(temp_output_dir, ignore_errors=True)

        return