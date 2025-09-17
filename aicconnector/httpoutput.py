import logging

import requests
from requests.exceptions import HTTPError, RequestException, Timeout
from starwit_aic_api.models.decision import Decision, Module, DecisionType
from visionapi.sae_pb2 import SaeMessage

from .config import HttpOutputConfig, LogLevel

logger = logging.getLogger(__name__)

class HttpOutput:
    def __init__(self, config: HttpOutputConfig, log_level: LogLevel) -> None:
        self.config = config
        logger.setLevel(log_level.value)

    def send_decision_message(self, sae_msg: SaeMessage, sae_id: str) -> None:
        decision_payload = self._create_decision_msg(sae_msg, sae_id)

        logger.info(f"Sending decision to cockpit: {self.config.target_endpoint}")
        logger.debug(f"Decision payload: {decision_payload}")
        try:
            if self.config.auth:
                # Get an access token if auth is configured
                token = requests.post(
                    self.config.auth.token_endpoint_url,
                    data={
                        'client_id': self.config.auth.client_id,
                        'username': self.config.auth.username,
                        'password': self.config.auth.password,
                        'grant_type': 'password',
                    }
                ).json().get('access_token')
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            else:
                headers = {"Content-Type": "application/json"}
            
            # Send the actual request
            response = requests.post(
                self.config.target_endpoint,
                data=decision_payload,
                headers=headers,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except Timeout:
            logger.error("The request timed out.")
        except HTTPError as http_err:
            logger.error(f"Request failed with status code: {http_err.response.status_code}")
            logger.error(f"Response content: {http_err.response.content}")
        except RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
        except Exception as err:
            logger.error(f"An unexpected error occurred: {err}")

    def _create_decision_msg(self, sae_msg: SaeMessage, sae_id: str) -> str:
        output_msg = Decision()
        output_msg.media_url = f'{self.config.minio.bucket_name}/{sae_id}/annotated.jpg'
        output_msg.module = Module()
        output_msg.module.name = self.config.module_name
        output_msg.acquisition_time = sae_msg.frame.timestamp_utc_ms

        # Forward camera geo location
        if sae_msg.frame.HasField('camera_location'):
            output_msg.camera_latitude = sae_msg.frame.camera_location.latitude
            output_msg.camera_longitude = sae_msg.frame.camera_location.longitude
        
        # type: ingore
        return output_msg.model_dump_json(by_alias=True, include={
            'acquisition_time': ...,
            'media_url': ...,
            'action_visualization_url': ...,
            'camera_latitude': ...,
            'camera_longitude': ...,
            'description': ...,
            'module': {
                'id': ...,
                'name': ...
            },
            'decision_type': {
                'id': ...,
                'name': ...
            }
        })