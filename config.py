from enum import Enum
from pathlib import Path

import pickledb
from pickledb import PickleDB
from pydantic import BaseModel


class PaginationMode(Enum):
    All = 1
    Auto = 2
    Manual = 3


class Website(BaseModel):
    version: str = "1.0"
    title: str = "揽月个人云盘"
    name: str = "揽月客"
    notice: str = ""
    icon: str = ""


class Preview(BaseModel):
    office: str = "pdf,docx,pptx"
    text: str = "txt"
    image: str = "jpg,jpeg,png"
    audio: str = "mp3"
    video: str = "mp4"
    auto_play_audio: bool = False
    auto_play_video: bool = False
    thumbnail: bool = True


class Fs(BaseModel):
    pagination_mode: int = 1
    pagination_size: int = 30
    max_upload_size: int = 1024 * 1024 * 1024 * 4
    max_download_size: int = 1024 * 1024 * 1024 * 4
    max_parallel: int = 3
    chunk_size: int = 1024 * 1024 * 30
    skip_files: str = ""


class Config(BaseModel):
    website: Website
    preview: Preview
    fs: Fs


class AppConfig:
    config: Config = None
    db_path: str = None
    db: PickleDB = None
    key: str = "config"

    @classmethod
    def init(cls, db_path):
        cls.db_path = db_path
        cls.db = pickledb.load(cls.db_path, auto_dump=True)

        if not Path(cls.db_path).exists():
            config_ = Config(website=Website(), preview=Preview(), fs=Fs())
            cls.set_config(config_.model_dump())
        else:
            cls.load_config()

    @classmethod
    def set_config(cls, conf: dict):
        config_ = Config(**conf)
        cls.config = config_
        cls.db.set(cls.key, config_.model_dump())

    @classmethod
    def load_config(cls):
        config_ = cls.db.get(cls.key)
        cls.config = Config(**config_)
