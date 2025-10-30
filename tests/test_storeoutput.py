import numpy as np
import pytest
from aicconnector.storeoutput import get_frame_from_sae_message
from aicconnector import storeoutput
from aicconnector.storeoutput import _annotate

class _Frame:
    def __init__(self, data: bytes):
        self.frame_data_jpeg = data

class _SaeMsg:
    def __init__(self, data: bytes):
        self.frame = _Frame(data)

def test_get_frame_from_sae_message_returns_numpy_array_with_correct_contents():
    data = b'\x00\x01\x02\xff\x10'
    sae = _SaeMsg(data)

    result = get_frame_from_sae_message(sae)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert result.shape == (len(data),)
    assert np.array_equal(result, np.frombuffer(data, np.uint8))

def test_get_frame_from_sae_message_handles_empty_bytes():
    data = b''
    sae = _SaeMsg(data)

    result = get_frame_from_sae_message(sae)

    assert isinstance(result, np.ndarray)
    assert result.size == 0
    assert result.shape == (0,)

def test_get_frame_from_sae_message_accepts_bytearray_like_objects():
    data = bytearray(b'\x10\x20\x30')
    sae = _SaeMsg(data)

    result = get_frame_from_sae_message(sae)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert np.array_equal(result, np.frombuffer(data, np.uint8))
    
class _BBox:
    def __init__(self, min_x, min_y, max_x, max_y):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y

class _Detection:
    def __init__(self, bbox, class_id, confidence, object_id=None):
        self.bounding_box = bbox
        self.class_id = class_id
        self.confidence = confidence
        self.object_id = object_id

def test__annotate_includes_object_id_in_label_when_present(monkeypatch):
    img = np.zeros((120, 160, 3), dtype=np.uint8)
    bbox = _BBox(0.2, 0.2, 0.6, 0.6)
    object_id_bytes = b'\x12\x34\x56\x78'
    detection = _Detection(bbox, "car", 0.4567, object_id=object_id_bytes)

    captured = {}

    def fake_rectangle(image, pt1, pt2, color=None, thickness=None, lineType=None):
        captured['rect_called'] = True
        return image

    def fake_putText(*args, **kwargs):
        text = args[1] if len(args) > 1 else kwargs.get('text')
        captured['text'] = text
        return args[0]

    monkeypatch.setattr(storeoutput.cv2, 'rectangle', fake_rectangle)
    monkeypatch.setattr(storeoutput.cv2, 'putText', fake_putText)

    _annotate(img, detection)

    expected_id = object_id_bytes.hex()[:4]
    expected_label = f'ID {expected_id} - {detection.class_id} - {round(detection.confidence, 2)}'
    assert captured.get('text') == expected_label
    
def test_draw_bounding_boxes_in_frame_calls_annotate_and_returns_encoded_bytes(monkeypatch):
    data = b'\x00\x01\x02'
    sae = _SaeMsg(data)
    det1 = _Detection(_BBox(0.1, 0.1, 0.2, 0.2), "car", 0.5)
    det2 = _Detection(_BBox(0.2, 0.2, 0.3, 0.3), "person", 0.7)
    sae.detections = [det1, det2]

    fake_image = np.zeros((10, 10, 3), dtype=np.uint8)

    def fake_imdecode(np_arr, flags):
        # ensure the buffer passed is what we expect
        assert isinstance(np_arr, np.ndarray)
        assert np.array_equal(np_arr, np.frombuffer(data, np.uint8))
        return fake_image

    monkeypatch.setattr(storeoutput.cv2, "imdecode", fake_imdecode)

    called = []
    def fake_annotate(image, detection):
        called.append((image, detection))
        return image
    monkeypatch.setattr(storeoutput, "_annotate", fake_annotate)

    encoded_bytes = b'FAKEJPEG'
    encoded_array = np.frombuffer(encoded_bytes, np.uint8)
    def fake_imencode(ext, image):
        assert ext == '.jpeg'
        assert image is fake_image
        return True, encoded_array
    monkeypatch.setattr(storeoutput.cv2, "imencode", fake_imencode)

    result = storeoutput.draw_bonding_boxes_in_frame(sae)

    assert result == encoded_bytes
    assert len(called) == 2
    assert called[0][1] is det1 and called[1][1] is det2

def test_draw_bounding_boxes_in_frame_handles_no_detections(monkeypatch):
    data = b'\x11\x22'
    sae = _SaeMsg(data)
    sae.detections = []

    fake_image = np.zeros((5, 5, 3), dtype=np.uint8)
    monkeypatch.setattr(storeoutput.cv2, "imdecode", lambda np_arr, flags: fake_image)

    annotated_called = False
    def fake_annotate(image, detection):
        nonlocal annotated_called
        annotated_called = True
        return image
    monkeypatch.setattr(storeoutput, "_annotate", fake_annotate)

    encoded_bytes = b'NO_DET'
    monkeypatch.setattr(storeoutput.cv2, "imencode", lambda ext, image: (True, np.frombuffer(encoded_bytes, np.uint8)))

    result = storeoutput.draw_bonding_boxes_in_frame(sae)

    assert result == encoded_bytes
    assert annotated_called is False

