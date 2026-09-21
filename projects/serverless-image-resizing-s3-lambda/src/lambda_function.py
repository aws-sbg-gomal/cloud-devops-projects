"""Resize JPEG and PNG images uploaded to an Amazon S3 source bucket."""

import io
import logging
import os
from pathlib import PurePosixPath
from urllib.parse import unquote_plus

import boto3
from PIL import Image, ImageOps, UnidentifiedImageError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)
S3 = boto3.client("s3")

DESTINATION_BUCKET = os.environ.get("DESTINATION_BUCKET", "")
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "resized/").strip("/")
MAX_WIDTH = int(os.environ.get("MAX_WIDTH", "800"))
MAX_HEIGHT = int(os.environ.get("MAX_HEIGHT", "800"))
JPEG_QUALITY = int(os.environ.get("JPEG_QUALITY", "85"))
MAX_INPUT_BYTES = int(os.environ.get("MAX_INPUT_BYTES", str(10 * 1024 * 1024)))

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png"}


def resize_image(image_bytes: bytes, suffix: str) -> tuple[bytes, str]:
    """Return resized image bytes and the correct response content type."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as original:
            image = ImageOps.exif_transpose(original)
            image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            if suffix in {".jpg", ".jpeg"}:
                if image.mode not in {"RGB", "L"}:
                    background = Image.new("RGB", image.size, "white")
                    if "A" in image.getbands():
                        background.paste(image, mask=image.getchannel("A"))
                    else:
                        background.paste(image)
                    image = background
                elif image.mode == "L":
                    image = image.convert("RGB")
                image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
                content_type = "image/jpeg"
            else:
                image.save(output, format="PNG", optimize=True)
                content_type = "image/png"
            return output.getvalue(), content_type
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("The S3 object is not a valid supported image") from error


def lambda_handler(event, context):
    """Process every S3 record delivered in one Lambda invocation."""
    if not DESTINATION_BUCKET:
        raise RuntimeError("DESTINATION_BUCKET environment variable is required")

    processed = []
    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = unquote_plus(record["s3"]["object"]["key"])
        suffix = PurePosixPath(source_key).suffix.lower()

        if suffix not in SUPPORTED_SUFFIXES:
            LOGGER.warning("Skipping unsupported object: s3://%s/%s", source_bucket, source_key)
            continue

        object_size = int(record["s3"]["object"].get("size", 0))
        if object_size and object_size > MAX_INPUT_BYTES:
            raise ValueError(f"Input object exceeds MAX_INPUT_BYTES: {source_key}")

        response = S3.get_object(Bucket=source_bucket, Key=source_key)
        image_bytes = response["Body"].read(MAX_INPUT_BYTES + 1)
        if len(image_bytes) > MAX_INPUT_BYTES:
            raise ValueError(f"Input object exceeds MAX_INPUT_BYTES: {source_key}")

        resized_bytes, content_type = resize_image(image_bytes, suffix)
        destination_key = f"{OUTPUT_PREFIX}/{source_key}" if OUTPUT_PREFIX else source_key

        S3.put_object(
            Bucket=DESTINATION_BUCKET,
            Key=destination_key,
            Body=resized_bytes,
            ContentType=content_type,
            Metadata={"source-bucket": source_bucket, "source-key": source_key},
        )
        LOGGER.info(
            "Resized s3://%s/%s to s3://%s/%s (%d bytes)",
            source_bucket,
            source_key,
            DESTINATION_BUCKET,
            destination_key,
            len(resized_bytes),
        )
        processed.append(destination_key)

    return {"processed": len(processed), "keys": processed}
