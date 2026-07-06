from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError


def load_and_strip_exif(raw: bytes, *, max_dimension: int | None = None) -> bytes:
    """Decode an image and re-encode without EXIF metadata."""
    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image",
        ) from None

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    if max_dimension is not None:
        image.thumbnail((max_dimension, max_dimension))

    buf = BytesIO()
    image.save(buf, format="JPEG", exif=b"")
    return buf.getvalue()
