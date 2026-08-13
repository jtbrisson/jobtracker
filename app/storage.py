"""Thin wrapper around an S3-compatible object store (Cloudflare R2, AWS S3,
Backblaze B2, MinIO, ...) used to store resume / cover letter / job
description files for each application.

Configured entirely through env vars (see .env.example):
  S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY,
  S3_BUCKET_NAME, S3_REGION

Everything is stored under a per-application "folder" (key prefix) so a
person can find an application's files in the bucket console too:
  applications/<application_id>/<field>/<uuid>-<original_filename>
"""
import uuid
from datetime import timedelta

import boto3
from botocore.client import Config as BotoConfig
from flask import current_app


def _client():
    cfg = current_app.config
    session = boto3.session.Session()
    kwargs = dict(
        service_name="s3",
        aws_access_key_id=cfg["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["S3_SECRET_ACCESS_KEY"],
        region_name=cfg.get("S3_REGION") or "auto",
        config=BotoConfig(signature_version="s3v4"),
    )
    if cfg.get("S3_ENDPOINT_URL"):
        kwargs["endpoint_url"] = cfg["S3_ENDPOINT_URL"]
    return session.client(**kwargs)


def is_configured():
    cfg = current_app.config
    return bool(cfg.get("S3_ACCESS_KEY_ID") and cfg.get("S3_SECRET_ACCESS_KEY") and cfg.get("S3_BUCKET_NAME"))


def upload_file(file_storage, *, application_id, field_name):
    """Upload a werkzeug FileStorage to the bucket.

    Returns (key, original_filename, content_type) to store on the model.
    """
    if not file_storage or not file_storage.filename:
        return None, None, None

    original_filename = file_storage.filename
    content_type = file_storage.content_type or "application/octet-stream"
    key = f"applications/{application_id}/{field_name}/{uuid.uuid4().hex}-{original_filename}"

    client = _client()
    client.upload_fileobj(
        file_storage.stream,
        current_app.config["S3_BUCKET_NAME"],
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return key, original_filename, content_type


def delete_file(key):
    if not key:
        return
    client = _client()
    client.delete_object(Bucket=current_app.config["S3_BUCKET_NAME"], Key=key)


def presigned_download_url(key, *, filename=None):
    if not key:
        return None
    client = _client()
    params = {"Bucket": current_app.config["S3_BUCKET_NAME"], "Key": key}
    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
    expiry = current_app.config.get("S3_PRESIGN_EXPIRY", 3600)
    return client.generate_presigned_url(
        "get_object", Params=params, ExpiresIn=expiry
    )
