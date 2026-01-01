"""
Digital Asset Management (DAM) schemas.
"""
from datetime import datetime
from typing import Any

from pydantic import Field

from indexer_api.db.models import AssetType
from indexer_api.schemas.base import BaseSchema


# ============================================================================
# DAM Metadata Schemas
# ============================================================================


class ExifData(BaseSchema):
    """EXIF metadata from images."""

    camera_make: str | None = None
    camera_model: str | None = None
    date_taken: datetime | None = None
    exposure_time: str | None = None
    f_number: float | None = None
    iso: int | None = None
    focal_length: float | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    orientation: int | None = None
    software: str | None = None


class AudioMetadata(BaseSchema):
    """Audio file metadata."""

    title: str | None = None
    artist: str | None = None
    album: str | None = None
    year: int | None = None
    track: int | None = None
    genre: str | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None


class DocumentMetadata(BaseSchema):
    """Document (PDF) metadata."""

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    creator: str | None = None
    producer: str | None = None
    page_count: int | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None


class DAMMetadata(BaseSchema):
    """Core DAM metadata stored in extra_metadata."""

    asset_type: AssetType
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    format: str | None = None
    codec: str | None = None
    bitrate: int | None = None
    frame_rate: float | None = None
    dominant_colors: list[str] | None = None
    exif: ExifData | None = None
    audio: AudioMetadata | None = None
    document: DocumentMetadata | None = None


# ============================================================================
# DAM Response Schemas
# ============================================================================


class DAMAssetResponse(BaseSchema):
    """Extended file response with DAM metadata."""

    id: str
    index_id: str
    path: str
    filename: str
    extension: str | None
    size_bytes: int
    created_time: datetime | None
    modified_time: datetime | None
    mime_type: str | None
    indexed_at: datetime
    dam: DAMMetadata | None = None


class DAMAssetDetail(DAMAssetResponse):
    """Detailed asset response with all metadata."""

    md5_hash: str | None = None
    sha256_hash: str | None = None
    quality_score: float | None = None


# ============================================================================
# DAM Search Schemas
# ============================================================================


class DAMSearch(BaseSchema):
    """Search/filter parameters for DAM assets."""

    asset_type: AssetType | None = None
    asset_types: list[AssetType] | None = None
    min_width: int | None = Field(None, ge=0)
    max_width: int | None = None
    min_height: int | None = Field(None, ge=0)
    max_height: int | None = None
    min_duration: float | None = Field(None, ge=0)
    max_duration: float | None = None
    has_exif: bool | None = None
    has_gps: bool | None = None
    camera_make: str | None = None
    date_taken_after: datetime | None = None
    date_taken_before: datetime | None = None
    color: str | None = Field(None, max_length=7, description="Hex color to match")
    format: str | None = None
    order_by: str = Field(
        default="filename",
        pattern=r"^(filename|size_bytes|modified_time|width|height|duration_seconds)$"
    )
    order_desc: bool = False


# ============================================================================
# DAM Statistics Schemas
# ============================================================================


class DAMStats(BaseSchema):
    """DAM statistics for an index."""

    index_id: str
    total_assets: int
    total_images: int
    total_videos: int
    total_audio: int
    total_documents: int
    total_other: int
    total_size_bytes: int
    total_size_human: str
    size_by_type: dict[str, int]
    format_breakdown: dict[str, int]
    resolution_distribution: dict[str, int]
    camera_breakdown: dict[str, int] | None = None
    avg_image_dimensions: dict[str, float] | None = None
    avg_video_duration: float | None = None
    avg_audio_duration: float | None = None


class DAMAnalysisJob(BaseSchema):
    """Response for starting a DAM analysis job."""

    job_id: str
    index_id: str
    status: str
    total_files_to_analyze: int
    message: str
