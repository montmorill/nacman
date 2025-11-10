from functools import cached_property
from typing import List, Any, Dict
from datetime import datetime, timedelta

import streamlit as st
from pyncm import apis
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from streamlit.delta_generator import DeltaGenerator


class AudioQuality(BaseModel):
    bitrate: int = Field(alias="br")
    file_id: int = Field(alias="fid")
    size: int
    volume_delta: float = Field(alias="vd")
    sample_rate: int = Field(alias="sr")


class BaseEntity(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    id: int
    name: str
    translations: List[str] = Field(alias="tns", default_factory=list)
    alias: List[str] = Field(alias="alia", default_factory=list)


class Artist(BaseEntity):
    pass


class Album(BaseEntity):
    pic_url: str


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
    # qualities: Dict[str, AudioQuality]

    @field_validator("publish_time", mode="before")
    @classmethod
    def parse_publish_time(cls, v: Any) -> datetime:
        return datetime.fromtimestamp(v / 1000) if isinstance(v, int) else v

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v: Any) -> timedelta:
        return timedelta(milliseconds=v) if isinstance(v, int) else v

    # @model_validator(mode="before")
    # @classmethod
    # def build_qualities(cls, data: Any) -> Any:
    #     if isinstance(data, dict):
    #         quality_mapping = {
    #             "sq": "super",
    #             "h": "high",
    #             "m": "medium",
    #             "l": "low"
    #         }
    #         data["qualities"] = {
    #             quality_mapping[field]: data[field]
    #             for field in quality_mapping.keys()
    #             if data.get(field) is not None
    #             and isinstance(data[field], dict)
    #         }
    #     return data

    @cached_property
    def title(self) -> str:
        return f"{self.name} - {', '.join(artist.name for artist in self.artists)}"

    @computed_field
    @cached_property
    def detail(self) -> Dict[str, Any]:
        return apis.track.GetTrackAudio([self.id])["data"][0]
