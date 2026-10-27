import numpy as np
import pytest
from PIL import Image
from api import coverage


def test_threshold_boundary_and_direction():
    p = np.array([[0, .649, .65, .651, 1]], dtype=np.float32)
    assert coverage._binary_mask(p).tolist() == [[0, 0, 1, 1, 1]]


def test_exact_new_artifact_is_selected():
    assert coverage._sha256(coverage.DEFAULT_MODEL_PATH) == coverage.EXPECTED_SHA256
    assert coverage.DEFAULT_MODEL_PATH.suffix == '.keras'
    assert coverage.THRESHOLD == .65


def test_preprocessing_and_invalid_output():
    seen = {}
    def model(batch, training=False):
        seen['batch'] = np.asarray(batch)
        return np.zeros((1, 320, 320, 1), dtype=np.float32)
    values = coverage._probabilities(model, Image.new('RGB', (120, 180), (255, 0, 128)))
    assert seen['batch'].shape == (1, 320, 320, 3)
    assert np.allclose(seen['batch'][0,0,0], [1, 0, 128/255])
    assert values.shape == (320,320)
    with pytest.raises(ValueError):
        coverage._probabilities(lambda *a,**k:np.full((1,320,320,1),np.nan),Image.new('RGB',(64,64)))


def test_native_coverage_mask_alignment_and_no_morphology(tmp_path, monkeypatch):
    # A one-pixel region must survive: do not silently apply the old cleanup.
    p = np.zeros((320,320), dtype=np.float32)
    p[0,0] = .7
    monkeypatch.setattr(coverage, '_load', lambda *a: object())
    monkeypatch.setattr(coverage, '_probabilities', lambda *a:p)
    photo = tmp_path/'input.png'
    Image.new('RGB',(640,320),(80,120,80)).save(photo)
    j=coverage.predict(image_path=str(photo),context={'artifact_dir':str(tmp_path/'artifacts')})
    assert j['value']['coverage_percent'] == pytest.approx(100/(320*320))
    assert j['details']['threshold'] == .65
    assert j['details']['confidence_calibrated'] is False
    mask = np.asarray(Image.open(j['artifacts']['coverage_mask']))
    assert mask.shape == (320,640)
    assert int((mask>0).sum()) == 2
