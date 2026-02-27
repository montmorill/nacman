from datetime import datetime, timedelta
from enum import StrEnum
from functools import cache, cached_property
from typing import Annotated, Any, Literal

import streamlit as st
from pydantic import BaseModel as _BaseModel
from pydantic import (BeforeValidator, ConfigDict, Field, ValidationError,
                      field_validator, model_validator)
from pydantic.alias_generators import to_camel
from pyncm.apis.album import GetAlbumComments
from pyncm.apis.track import GetTrackAudio, GetTrackLyrics

Timestamp = Annotated[datetime, BeforeValidator(
    lambda val: datetime.fromtimestamp(val / 1000)
    if isinstance(val, int) else val)]


class BaseModel(_BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
    )


class BaseEntity(BaseModel):
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
        response = GetTrackAudio([self.id], bitrate=info.bit_rate)
        try:
            return AudioDetail(**response["data"][0])  # type: ignore
        except KeyError:
            st.error(f"Failed to get audio detail for track {self.id}")
            st.json(response)
        except ValidationError:
            return None

    @cached_property
    def lyrics(self) -> TrackLyrics:
        response = GetTrackLyrics(str(self.id))
        return TrackLyrics(**response)  # type: ignore


class Track(BaseTrack):
    album: BaseAlbum = Field(alias="al")
    is_single: bool = Field(alias="single")
    publish_time: Timestamp


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
    tag: None = None
    award_tags: None
    display_tags: None
    publish_time: Timestamp


class Album(BaseModel):
    songs: list[BaseTrack]
    info: AlbumInfo = Field(alias="album")

    @cached_property
    def comments(self) -> list["Comment"]:
        response = GetAlbumComments(str(self.info.id))
        comments = AlbumComments(**response)  # type: ignore
        return comments.hot_comments + comments.comments


class User(BaseModel):
    user_id: int
    nickname: str
    avatar_url: str


class Comment(BaseModel):
    comment_id: int
    user: User
    content: str
    rich_content: str
    time: Timestamp
    time_str: str
    liked_count: int
    parent_comment_id: int = 0


class AlbumComments(BaseModel):
    is_musician: bool
    cnum: Literal[0]
    top_comments: list[Comment] = Field(max_length=0)
    hot_comments: list[Comment]
    more_hot: bool
    comment_banner: None
    comments: list[Comment]
    total_count: int | None = None
    more: bool
