import pytest
from upscale.server import app as flask_app

@pytest.fixture
def app():
    yield flask_app