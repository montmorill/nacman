from datetime import datetime, timedelta
from enum import StrEnum
from functools import cache, cached_property
from typing import Any, List, Dict

from pyncm import apis
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel


class AudioInfo(BaseModel):
    size: int
    bitrate: int = Field(alias="br")
    file_id: int = Field(alias="fid")
    volume_delta: float = Field(alias="vd")
    sample_rate: int = Field(alias="sr")


class BaseEntity(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    id: int
    name: str
    translations: List[str] = Field(alias="tns", default_factory=list)
    alias: List[str] = Field(alias="alia", default_factory=list)

    def __hash__(self) -> int:
        return hash(self.id)


class Artist(BaseEntity):
    pass


class Album(BaseEntity):
    pic_url: str


class AudioQuality(StrEnum):
    STANDARD = "standard"
    HIGHER = "higher"
    EXHIGH = "exhigh"
    LOSSLESS = "lossless"


class Track(BaseEntity):
    artists: List[Artist] = Field(alias="ar")
    album: Album = Field(alias="al")
    publish_time: datetime
    duration: timedelta = Field(alias="dt")
    track_number: int = Field(alias="no")
    is_single: bool = Field(alias="single")
    music_video_id: int = Field(alias="mv")
    radio_program_id: int = Field(alias="djId")
    popularity: int = Field(alias="pop")
    qualities: Dict[AudioQuality, AudioInfo]

    @field_validator("publish_time", mode="before")
    @classmethod
    def parse_publish_time(cls, v: Any) -> datetime:
        return datetime.fromtimestamp(v / 1000) if isinstance(v, int) else v

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v: Any) -> timedelta:
        return timedelta(milliseconds=v) if isinstance(v, int) else v

    @model_validator(mode="before")
    @classmethod
    def build_qualities(cls, data: Any) -> Any:
        if isinstance(data, dict):
            quality_mapping = {
                "l":  AudioQuality.STANDARD,    # 128000
                "m":  AudioQuality.HIGHER,      # 192000
                "h":  AudioQuality.EXHIGH,      # 320000
                "sq": AudioQuality.LOSSLESS     # 321000+
            }
            data["qualities"] = {
                quality_mapping[field]: data[field]
                for field in quality_mapping.keys()
                if data.get(field) is not None
                and isinstance(data[field], dict)
            }
        return data

    @property
    def title(self) -> str:
        return f"{self.name} - {', '.join(artist.name for artist in self.artists)}"

    @cache
    def detail(self, quality: AudioQuality = AudioQuality.STANDARD) -> Dict[str, Any]:
        if quality in self.qualities:
            bitrate = self.qualities[quality].bitrate
        else:
            # fallback to highest quality
            bitrate = list(self.qualities.values())[-1].bitrate
        data = apis.track.GetTrackAudio([self.id], bitrate=bitrate)
        return data["data"][0]  # type: ignore

    @cached_property
    def lyrics(self) -> str:
        return apis.track.GetTrackLyrics(str(self.id))  # type: ignore
