import logging
import signal
import threading

from prometheus_client import Counter, Histogram, start_http_server
from visionlib.pipeline.consumer import RedisConsumer

from .aicconnector import AicConnector
from .config import AicConnectorConfig

logger = logging.getLogger(__name__)

REDIS_PUBLISH_DURATION = Histogram('aic_connector_publish_duration', 'The time it takes to push a message onto the Redis stream',
                                   buckets=(0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25))
FRAME_COUNTER = Counter('aic_connector_frame_counter', 'How many frames have been consumed from the Redis input stream')

def run_stage():

    stop_event = threading.Event()

    # Register signal handlers
    def sig_handler(signum, _):
        signame = signal.Signals(signum).name
        print(f'Caught signal {signame} ({signum}). Exiting...')
        stop_event.set()

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    # Load config from settings.yaml / env vars
    CONFIG = AicConnectorConfig()

    logger.setLevel(CONFIG.log_level.value)

    logger.info(f'Starting prometheus metrics endpoint on port {CONFIG.prometheus_port}')

    start_http_server(CONFIG.prometheus_port)

    logger.info(f'Starting aic connector for computer vision. Config: {CONFIG.model_dump_json(indent=2)}')

    aic_connector = AicConnector(CONFIG)

    consume = RedisConsumer(CONFIG.redis_input.host, CONFIG.redis_input.port, 
                            stream_keys=[f'{CONFIG.redis_input.stream_prefix}:{stream_id}' for stream_id in CONFIG.redis_input.stream_ids])
    
    with consume:
        for stream_key, proto_data in consume():
            if stop_event.is_set():
                break

            if stream_key is None:
                continue

            logger.debug(f'Received sae message from {stream_key}')

            FRAME_COUNTER.inc()

            aic_connector.get(proto_data)