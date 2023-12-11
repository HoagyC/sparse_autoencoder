"""Utility functions for the project."""
import json
import os
from pathlib import Path
import warnings

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client


BUCKET_NAME = "sparse-autoencoder-repo"


def get_client() -> S3Client:
    """Authenticate with AWS."""
    with Path("secrets.json").open("rb") as f:
        secrets = json.load(f)

    return boto3.client(
        "s3",  # type: ignore
        aws_access_key_id=secrets["access_key"],
        aws_secret_access_key=secrets["secret_key"],
    )


def upload_to_aws(local_file_name: str) -> None:
    """Upload a file to an S3 bucket.

    :param local_file_name: File to upload
    """
    s3 = get_client()
    local_file_path = Path(local_file_name)
    try:
        if local_file_path.is_dir():
            _upload_directory(local_file_path, s3)
        else:
            s3.upload_file(str(local_file_name), BUCKET_NAME, str(local_file_name))
    except FileNotFoundError:
        err_str = f"File intended for upload {local_file_name} not found"
        raise FileNotFoundError(err_str) from None


def _upload_directory(path: Path, s3_client: S3Client) -> None:
    """Upload a directory to an S3 bucket.

    :param path: Directory to upload
    :param s3_client: S3 client
    """
    for root, _, files in os.walk(path):
        for file_name in files:
            full_file_name = Path(root) / file_name
            try:
                s3_client.upload_file(str(full_file_name), BUCKET_NAME, str(full_file_name))
            except FileNotFoundError:
                err_str = f"File intended for upload {full_file_name} not found"
                raise FileNotFoundError(err_str) from None


def download_from_aws(files: str | list[str], *, force_redownload: bool = False) -> None:
    """Download a file from an S3 bucket.

    :param files: List of files to download
    :param force_redownload: If True, will download even if the file already exists
    """
    s3 = get_client()

    file_paths = [Path(files)] if isinstance(files, str) else [Path(f) for f in files]

    if not force_redownload:
        file_paths = [f for f in file_paths if not f.exists()]

    for filename in file_paths:
        try:
            parent_dir = filename.parent
            if not parent_dir.exists() and parent_dir != Path():
                parent_dir.mkdir(parents=True)
            with filename.open("wb") as f:
                s3.download_fileobj(BUCKET_NAME, str(filename), f)

        except ClientError:  # noqa: PERF203
            warnings.warn(f"File {filename} not found in S3 bucket", stacklevel=2)
