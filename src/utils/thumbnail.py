import uuid
from datetime import datetime
import mimetypes
from pathlib import Path
from PIL import Image
import cv2
import os
from typing import Union


async def set_thumbnail(syspath: str, **kwargs):
    if Path(syspath).exists() and Path(syspath).is_file():
        create_time: float = os.path.getctime(syspath)
        create_time: datetime = datetime.fromtimestamp(create_time)
        mime_type: str = mimetypes.guess_type(syspath)[0]
        size = os.path.getsize(syspath)
        dir_path: Path = Path("data/thumbnail").joinpath(str(create_time.year)).joinpath(str(create_time.month)).absolute()
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        if mime_type:
            ident = str(uuid.uuid3(uuid.NAMESPACE_OID, f"{Path(syspath).name}_{create_time}_{mime_type}_{size}"))
            if mime_type.startswith("image/"):
                suffix: str = Path(syspath).suffix
                file_path: str = f"{dir_path.joinpath(ident)}{suffix}"
                if not Path(file_path).exists() and size > 0:
                    try:
                        img = Image.open(syspath)
                        img.thumbnail((800, 800))
                        img.save(file_path)
                    except:
                        pass
            if mime_type.startswith("video/"):
                file_path = f"{dir_path.joinpath(ident)}.jpg"
                if not Path(file_path).exists() and size > 0:
                    video = cv2.VideoCapture(syspath)
                    frame_count: float = video.get(cv2.CAP_PROP_FRAME_COUNT)
                    frame_pos = int(frame_count / 4)
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                    success, image = video.read()
                    if success:
                        img = Image.fromarray(image.astype("uint8")).convert("RGB")
                        img.thumbnail((800, 800))
                        img.save(file_path)


async def get_thumbnail(syspath: str, **kwargs) -> Union[str, None]:
    if Path(syspath).exists() and Path(syspath).is_file():
        create_time: float = os.path.getctime(syspath)
        create_time: datetime = datetime.fromtimestamp(create_time)
        mime_type: str = mimetypes.guess_type(syspath)[0]
        size = os.path.getsize(syspath)
        if mime_type:
            ident = str(uuid.uuid3(uuid.NAMESPACE_OID, f"{Path(syspath).name}_{create_time}_{mime_type}_{size}"))
            worker = os.path.abspath(".")
            if mime_type.startswith("image/"):
                suffix: str = Path(syspath).suffix
                dir_path: str = f"thumbnail/{str(create_time.year)}/{str(create_time.month)}/{ident}{suffix}"
                if not Path(worker).joinpath("data/" + dir_path).exists():
                    return None
                return "/" + dir_path
            elif mime_type.startswith("video/"):
                dir_path: str = f"thumbnail/{str(create_time.year)}/{str(create_time.month)}/{ident}.jpg"
                if not Path(worker).joinpath("data/" + dir_path).exists():
                    return None
                return "/" + dir_path
            else:
                return None
        else:
            return None
