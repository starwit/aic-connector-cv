import pytest
from unittest.mock import MagicMock, patch
from aicconnector.httpoutput import HttpOutput
from aicconnector.config import HttpOutputConfig, MinioConfig, LogLevel, AuthConfig

class DummySaeMessage:
    class Frame:
        timestamp_utc_ms = 1234567890
        def HasField(self, field):
            return field == 'camera_location'
        class CameraLocation:
            latitude = 42.0
            longitude = -71.0
        camera_location = CameraLocation()
    frame = Frame()

def make_config(auth=False):
    minio = MinioConfig(endpoint='http://minio', user='user', password='pass', bucket_name='bucket', secure=False)
    if auth:
        auth_cfg = AuthConfig(token_endpoint_url='http://auth', client_id='cid', username='user', password='pass')
    else:
        auth_cfg = None
    return HttpOutputConfig(target_endpoint='http://target', timeout=5, module_name='mod', auth=auth_cfg, minio=minio)

def test_create_decision_msg():
    config = make_config()
    http_output = HttpOutput(config, LogLevel.INFO)
    msg = DummySaeMessage()
    result = http_output._create_decision_msg(msg, 'sae_id')
    assert result is not None

def test_send_decision_message_no_auth(monkeypatch):
    config = make_config()
    http_output = HttpOutput(config, LogLevel.INFO)
    msg = DummySaeMessage()
    with patch('aicconnector.httpoutput.requests.post') as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()
        mock_post.return_value.json.return_value = {}
        http_output.send_decision_message(msg, 'sae_id')
        mock_post.assert_called()

def test_send_decision_message_with_auth(monkeypatch):
    config = make_config(auth=True)
    http_output = HttpOutput(config, LogLevel.INFO)
    msg = DummySaeMessage()
    with patch('aicconnector.httpoutput.requests.post') as mock_post:
        # First call for token, second for actual post
        mock_post.side_effect = [MagicMock(json=lambda: {'access_token': 'tok'}), MagicMock(raise_for_status=MagicMock())]
        http_output.send_decision_message(msg, 'sae_id')
        assert mock_post.call_count == 2

def test_send_decision_message_timeout(monkeypatch):
    config = make_config()
    http_output = HttpOutput(config, LogLevel.INFO)
    msg = DummySaeMessage()
    with patch('aicconnector.httpoutput.requests.post', side_effect=Exception('Timeout')):
        http_output.send_decision_message(msg, 'sae_id')
