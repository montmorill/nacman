from datetime import datetime, timedelta
from enum import StrEnum
from functools import cache, cached_property
from typing import Any

from pydantic import (BaseModel, ConfigDict, Field, ValidationError,
                      field_validator, model_validator)
from pydantic.alias_generators import to_camel
from pyncm import apis


class BaseEntity(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )

    id: int
    name: str
    translations: list[str] = Field(alias="tns", default_factory=list)
    alias: list[str] = Field(alias="alia", default_factory=list)

    def __hash__(self) -> int:
        return hash(self.id)


class Artist(BaseEntity):
    pass


class BaseAlbum(BaseEntity):
    pic_url: str


class AudioQuality(StrEnum):
    STANDARD = "standard"
    HIGHER = "higher"
    EXHIGH = "exhigh"
    LOSSLESS = "lossless"


class AudioInfo(BaseModel):
    size: int
    bit_rate: int = Field(alias="br")
    file_id: int = Field(alias="fid")
    volume_delta: float = Field(alias="vd")
    sample_rate: int = Field(alias="sr")


class AudioDetail(BaseModel):
    id: int
    url: str
    type: str
    level: AudioQuality | None = None
    bit_rate: int = Field(alias="br")
    simple_rate: int = Field(alias="sr")
    size: int
    md5: str
    gain: float | None = None
    peak: float | None = None
    closed_gain: float | None = None
    closed_peak: float | None = None


class LyricData(BaseModel):
    version: int = 0
    text: str = Field(alias="lyric", default="")


class TrackLyrics(BaseModel):
    original: LyricData = Field(alias="lrc")
    translated: LyricData = Field(alias="tlyric", default_factory=LyricData)
    romanized: LyricData = Field(alias="romalrc", default_factory=LyricData)


class BaseTrack(BaseEntity):
    artists: list[Artist] = Field(alias="ar")
    duration: timedelta = Field(alias="dt")
    track_number: int = Field(alias="no")
    music_video_id: int = Field(alias="mv")
    radio_program_id: int = Field(alias="djId")
    popularity: int = Field(alias="pop")
    qualities: dict[AudioQuality, AudioInfo]

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
                for field in quality_mapping
                if data.get(field) is not None
                and isinstance(data[field], dict)
            }
        return data

    @cached_property
    def highest_quality(self) -> AudioQuality:
        return max(
            self.qualities.keys(),
            key=lambda k: self.qualities[k].bit_rate
        )

    @cache
    def detail(self, quality: AudioQuality) -> AudioDetail | None:
        if (info := self.qualities.get(quality)) is None:
            info = self.qualities[self.highest_quality]
        response = apis.track.GetTrackAudio([self.id], bitrate=info.bit_rate)
        try:
            return AudioDetail(**response["data"][0])# type: ignore
        except ValidationError:
            return None

    @cached_property
    def lyrics(self) -> TrackLyrics:
        response = apis.track.GetTrackLyrics(str(self.id))
        return TrackLyrics(**response)  # type: ignore


class Track(BaseTrack):
    album: BaseAlbum = Field(alias="al")
    publish_time: datetime
    is_single: bool = Field(alias="single")

    @field_validator("publish_time", mode="before")
    @classmethod
    def parse_publish_time(cls, v: Any) -> datetime:
        return datetime.fromtimestamp(v / 1000) if isinstance(v, int) else v


class AlbumInfo(BaseAlbum):
    blur_pic_url: str
    artist: Artist
    artists: list[Artist]
    company: str
    company_id: int = 0
    brief_desc: str = ""
    description: str | None = None
    type: str
    sub_type: str
    size: int
    tag: str = ""
    award_tags: None
    display_tags: None


class Album(BaseModel):
    songs: list[BaseTrack]
    info: AlbumInfo = Field(alias="album")
