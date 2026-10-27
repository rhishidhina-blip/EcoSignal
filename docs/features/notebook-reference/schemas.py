"""Pydantic request and response schemas through Feature 16."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


class SampleCreate(ApiModel):
    study_area_id: str | None = None
    user_id: str | None = None
    captured_at: datetime
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    substrate_type: str | None = Field(default=None, max_length=64)
    site_type: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=4000)
    status: NonEmptyString = "submitted"

    @model_validator(mode="after")
    def coordinates_are_paired(self) -> "SampleCreate":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class SampleUpdate(ApiModel):
    study_area_id: str | None = None
    user_id: str | None = None
    captured_at: datetime | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    substrate_type: str | None = Field(default=None, max_length=64)
    site_type: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=4000)
    status: NonEmptyString | None = None

    @model_validator(mode="after")
    def coordinates_are_paired_when_both_in_payload(self) -> "SampleUpdate":
        fields = self.model_fields_set
        if ("latitude" in fields) != ("longitude" in fields):
            raise ValueError("patch latitude and longitude together")
        if "latitude" in fields and ((self.latitude is None) != (self.longitude is None)):
            raise ValueError("latitude and longitude must both be values or both be null")
        return self


class SampleRead(ApiModel):
    sample_id: str = Field(validation_alias="id")
    study_area_id: str | None
    user_id: str | None
    captured_at: datetime
    latitude: float | None
    longitude: float | None
    substrate_type: str | None
    site_type: str | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class PredictionCreate(ApiModel):
    model_type: NonEmptyString
    model_version: NonEmptyString
    predicted_value: dict[str, Any]
    confidence: float | None = Field(default=None, ge=0, le=1)
    status: NonEmptyString = "completed"
    warnings: list[str] = Field(default_factory=list)
    is_placeholder: bool = False

    @model_validator(mode="after")
    def placeholder_is_explicit(self) -> "PredictionCreate":
        if "placeholder" in self.model_version.lower() and not self.is_placeholder:
            raise ValueError(
                "placeholder model versions must set is_placeholder=true"
            )
        return self


class PredictionRead(ApiModel):
    prediction_id: str = Field(validation_alias="id")
    sample_id: str
    model_type: str
    model_version: str
    predicted_value: dict[str, Any] = Field(validation_alias="predicted_value_json")
    confidence: float | None
    status: str
    warnings: list[str] = Field(validation_alias="warnings_json")
    is_placeholder: bool
    created_at: datetime


class AssetRead(ApiModel):
    asset_id: str = Field(validation_alias="id")
    sample_id: str
    asset_type: str
    storage_path: str
    mime_type: str
    checksum: str
    width: int | None
    height: int | None
    created_by: str | None
    source_asset_id: str | None
    original_filename: str | None
    created_at: datetime


class CoverageAnalysisRequest(ApiModel):
    image_asset_id: NonEmptyString
    requested_by: NonEmptyString = "api-user"


class CorrectionCreate(ApiModel):
    field_name: NonEmptyString
    proposed_value: Any | None = None
    proposed_asset_id: str | None = None
    correction_method: str | None = Field(default=None, max_length=64)
    reason: str = Field(min_length=10, max_length=4000)
    submitted_by: NonEmptyString


class CorrectionRead(ApiModel):
    correction_id: str = Field(validation_alias="id")
    sample_id: str
    prediction_id: str
    field_name: str
    original_value: Any | None = Field(validation_alias="original_value_json")
    proposed_value: Any | None = Field(validation_alias="proposed_value_json")
    proposed_asset_id: str | None
    correction_method: str | None
    reason: str
    submitted_by: str
    status: str
    created_at: datetime
    updated_at: datetime
    withdrawn_at: datetime | None


class CorrectionWithdrawRequest(ApiModel):
    requested_by: NonEmptyString


class ReviewDecisionCreate(ApiModel):
    reviewer_id: NonEmptyString
    decision: str
    reviewer_notes: str | None = Field(default=None, max_length=4000)
    adjusted_value: Any | None = None
    dataset_version_id: str | None = None

    @model_validator(mode="after")
    def valid_decision(self) -> "ReviewDecisionCreate":
        allowed = {"approved", "rejected", "needs_more_evidence"}
        self.decision = self.decision.strip().lower()
        if self.decision not in allowed:
            raise ValueError(f"decision must be one of: {', '.join(sorted(allowed))}")
        if self.decision != "approved" and not (self.reviewer_notes or "").strip():
            raise ValueError("rejected and needs_more_evidence decisions require reviewer_notes")
        return self


class ReviewRead(ApiModel):
    review_id: str = Field(validation_alias="id")
    correction_id: str
    reviewer_id: str
    decision: str
    reviewer_notes: str | None
    reviewed_value: Any | None = Field(validation_alias="reviewed_value_json")
    assigned_dataset_version_id: str | None
    reviewed_at: datetime


class DatasetStagingRead(ApiModel):
    staging_item_id: str = Field(validation_alias="id")
    correction_id: str
    sample_id: str
    prediction_id: str
    field_name: str
    verified_value: Any | None = Field(validation_alias="verified_value_json")
    annotation_asset_id: str | None
    annotation_source: str
    approved_by: list[str] = Field(validation_alias="approved_by_json")
    status: str
    staged_at: datetime


class ReviewQueueItem(ApiModel):
    correction_id: str
    sample_id: str
    prediction_id: str
    field_name: str
    original_value: Any | None
    proposed_value: Any | None
    proposed_asset_id: str | None
    reason: str
    correction_status: str
    prediction_confidence: float | None
    approvals_received: int
    approvals_required: int
    created_at: datetime


class ReviewDetail(ApiModel):
    correction: CorrectionRead
    prediction: PredictionRead
    sample: SampleRead
    assets: list[AssetRead]
    previous_corrections: list[CorrectionRead]
    reviews: list[ReviewRead]
    staging_item: DatasetStagingRead | None
    review_requirements: dict[str, Any]


class ReviewDecisionResult(ApiModel):
    correction: CorrectionRead
    review: ReviewRead
    staging_item: DatasetStagingRead | None
    approvals_received: int
    approvals_required: int


class DatasetVersionCreate(ApiModel):
    name: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9_.-]+$")
    parent_version_id: str | None = None
    description: str | None = Field(default=None, max_length=4000)
    created_by: NonEmptyString


class DatasetVersionRead(ApiModel):
    dataset_version_id: str = Field(validation_alias="id")
    name: str
    parent_version_id: str | None
    status: str
    description: str | None
    created_by: str
    created_at: datetime
    frozen_at: datetime | None
    manifest_checksum: str | None


class DatasetItemCreate(ApiModel):
    staging_item_id: NonEmptyString
    image_asset_id: NonEmptyString
    split: str
    site_group: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def valid_split(self) -> "DatasetItemCreate":
        self.split = self.split.strip().lower()
        if self.split not in {"train", "validation", "test"}:
            raise ValueError("split must be train, validation, or test")
        return self


class DatasetItemRead(ApiModel):
    dataset_item_id: str = Field(validation_alias="id")
    dataset_version_id: str
    staging_item_id: str
    sample_id: str
    image_asset_id: str
    annotation_asset_id: str | None
    split: str
    annotation_source: str
    approved_correction_id: str
    site_group: str
    verified_value: Any | None = Field(validation_alias="verified_value_json")
    added_at: datetime


class DatasetExportCreate(ApiModel):
    export_format: str = "zip"

    @model_validator(mode="after")
    def valid_format(self) -> "DatasetExportCreate":
        self.export_format = self.export_format.strip().lower()
        if self.export_format not in {"zip", "csv", "json", "geojson"}:
            raise ValueError("export_format must be zip, csv, json, or geojson")
        return self


class DatasetExportRead(ApiModel):
    export_id: str = Field(validation_alias="id")
    dataset_version_id: str
    export_format: str
    storage_path: str
    checksum: str
    status: str
    item_count: int
    created_at: datetime


class AuditEventRead(ApiModel):
    event_id: str = Field(validation_alias="id")
    event_type: str
    entity_type: str
    entity_id: str
    sample_id: str | None
    actor_id: str | None
    payload: dict[str, Any] = Field(validation_alias="payload_json")
    previous_event_hash: str | None
    event_hash: str
    created_at: datetime


class ModelRegistryCreate(ApiModel):
    model_type: NonEmptyString
    version: NonEmptyString
    status: str
    dataset_version_id: str | None = None
    artifact_path: str | None = Field(default=None, max_length=1000)
    validation_status: NonEmptyString = "pending"
    card: dict[str, Any]
    metrics: dict[str, Any] = Field(default_factory=dict)
    threshold: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_registry(self) -> "ModelRegistryCreate":
        allowed = {"development", "validation_candidate", "production_candidate", "production", "retired"}
        self.status = self.status.strip().lower()
        if self.status not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        required = {"name", "purpose", "input", "output", "training_data", "validation_data", "known_failure_cases", "intended_use", "prohibited_use"}
        missing = sorted(required - self.card.keys())
        if missing:
            raise ValueError(f"model card missing fields: {', '.join(missing)}")
        return self


class ModelRegistryUpdate(ApiModel):
    status: str | None = None
    dataset_version_id: str | None = None
    artifact_path: str | None = Field(default=None, max_length=1000)
    validation_status: str | None = None
    card: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    threshold: float | None = Field(default=None, ge=0, le=1)


class ModelRegistryRead(ApiModel):
    model_id: str = Field(validation_alias="id")
    model_type: str
    version: str
    status: str
    dataset_version_id: str | None
    artifact_path: str | None
    validation_status: str
    card: dict[str, Any] = Field(validation_alias="card_json")
    metrics: dict[str, Any] = Field(validation_alias="metrics_json")
    threshold: float | None
    created_at: datetime
    updated_at: datetime


class ActiveLearningRecalculate(ApiModel):
    formula_version: NonEmptyString = "active_learning_priority_v0"
    weights: dict[str, float] = Field(default_factory=lambda: {
        "model_uncertainty": .30, "geographic_uncertainty": .25,
        "class_rarity": .20, "sample_quality": .15, "study_importance": .10,
    })

    @model_validator(mode="after")
    def valid_weights(self) -> "ActiveLearningRecalculate":
        expected = {"model_uncertainty", "geographic_uncertainty", "class_rarity", "sample_quality", "study_importance"}
        if set(self.weights) != expected or any(not 0 <= value <= 1 for value in self.weights.values()):
            raise ValueError("weights must provide all five components with values from 0 to 1")
        if abs(sum(self.weights.values()) - 1.0) > 1e-6:
            raise ValueError("active-learning weights must sum to 1")
        return self


class ActiveLearningUpdate(ApiModel):
    status: str

    @model_validator(mode="after")
    def valid_status(self) -> "ActiveLearningUpdate":
        self.status = self.status.strip().lower()
        if self.status not in {"queued", "assigned", "completed", "dismissed"}:
            raise ValueError("invalid active-learning status")
        return self


class ActiveLearningRead(ApiModel):
    item_id: str = Field(validation_alias="id")
    sample_id: str
    queue_type: str
    priority_score: float
    priority_reasons: list[str] = Field(validation_alias="priority_reasons_json")
    components: dict[str, float] = Field(validation_alias="components_json")
    formula_version: str
    status: str
    updated_at: datetime


class ReanalysisRequest(ApiModel):
    asset_id: NonEmptyString
    model_type: NonEmptyString
    model_version: NonEmptyString


class QualityAssessmentRead(ApiModel):
    quality_assessment_id: str = Field(validation_alias="id")
    sample_id: str
    asset_id: str
    quality_score: float
    decision: str
    metrics: dict[str, Any] = Field(validation_alias="metrics_json")
    warnings: list[str] = Field(validation_alias="warnings_json")
    thresholds: dict[str, Any] = Field(validation_alias="thresholds_json")
    quality_version: str
    created_at: datetime


class AnalyzeSampleRequest(ApiModel):
    sample_id: NonEmptyString
    asset_id: NonEmptyString
    run_models: list[str] = Field(min_length=1)
    pipeline_version: NonEmptyString = "ecosignal_pipeline_v1"
    geospatial_layer_versions: dict[str, str] = Field(default_factory=dict)


class ConfidenceCreate(ApiModel):
    analysis_run_id: str | None = None
    components: dict[str, float | None]
    confidence_version: NonEmptyString = "sample_confidence_v0"
    weights: dict[str, float] | None = None


class ConfidenceRead(ApiModel):
    confidence_assessment_id: str = Field(validation_alias="id")
    sample_id: str
    analysis_run_id: str | None
    components: dict[str, Any] = Field(validation_alias="components_json")
    overall_confidence: float | None
    weights: dict[str, float] = Field(validation_alias="weights_json")
    limitations: list[str] = Field(validation_alias="limitations_json")
    confidence_version: str
    created_at: datetime
