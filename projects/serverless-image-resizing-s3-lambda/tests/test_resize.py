import io
import importlib.util
import os
import sys
import types
from pathlib import Path

from PIL import Image


class FakeS3:
    def __init__(self):
        self.objects = {}


fake_boto3 = types.SimpleNamespace(client=lambda service: FakeS3())
sys.modules.setdefault("boto3", fake_boto3)
os.environ.setdefault("DESTINATION_BUCKET", "test-output")

module_path = Path(__file__).parents[1] / "src" / "lambda_function.py"
spec = importlib.util.spec_from_file_location("lambda_function", module_path)
lambda_function = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lambda_function)


def make_image(image_format="JPEG", size=(1600, 1200)):
    stream = io.BytesIO()
    Image.new("RGB", size, "orange").save(stream, image_format)
    return stream.getvalue()


def test_jpeg_is_resized_within_limits():
    output, content_type = lambda_function.resize_image(make_image(), ".jpg")
    with Image.open(io.BytesIO(output)) as image:
        assert image.width <= 800
        assert image.height <= 800
    assert content_type == "image/jpeg"


def test_png_keeps_png_format():
    output, content_type = lambda_function.resize_image(make_image("PNG"), ".png")
    with Image.open(io.BytesIO(output)) as image:
        assert image.format == "PNG"
    assert content_type == "image/png"
