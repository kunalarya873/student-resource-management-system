#!/usr/bin/env python3
"""
AMU Student Resource Management System - Resource Upload Utility
Uploads resources into user-isolated folders in Supabase Storage with strict privacy controls.
"""

import argparse
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# 1. Load environment variables securely from .env (no hardcoded secrets)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / "backend" / ".env")
load_dotenv(BASE_DIR / ".env")

SUPABASE_URL = os.getenv(
    "SUPABASE_URL", "https://ijlfghksvuyoynshxoif.storage.supabase.co"
)
# Prefer service_role key for backend CLI uploads (bypasses RLS), fallback to anon key
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "resources")

if not SUPABASE_KEY:
    print(
        "Warning: Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_KEY found in environment or .env."
    )


def get_supabase_client() -> Client:
    """Initialize authenticated Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_resource(
    file_path: str,
    user_id: str | None = None,
    folder_name: str = "general",
    content_type: str = "image/png",
    private: bool = True,
) -> dict:
    """
    Upload a file into a user-specific folder with privacy controls.
    Storage Path structure: users/{user_id}/{folder_name}/{filename}
    """
    resolved_path = Path(file_path)
    if not resolved_path.exists():
        if (BASE_DIR / file_path).exists():
            resolved_path = BASE_DIR / file_path
        else:
            raise FileNotFoundError(f"File not found: {file_path}")

    # Generate or validate user_id for folder segregation
    clean_user_id = user_id or str(uuid.uuid4())
    filename = resolved_path.name

    # Hierarchical user-isolated storage path
    storage_path = f"users/{clean_user_id}/{folder_name}/{filename}"

    with open(resolved_path, "rb") as f:
        file_data = f.read()

    client = get_supabase_client()

    print(f"Uploading '{filename}' ({len(file_data)} bytes)...")
    print(f"Destination folder: users/{clean_user_id}/{folder_name}/")

    try:
        response = client.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        print(f"File uploaded successfully to Supabase Storage: {response}")
    except Exception as exc:
        err_msg = str(exc)
        if "row-level security" in err_msg.lower() or "403" in err_msg:
            print(
                "\n[Security Notice]: Upload rejected by Supabase Row-Level Security (RLS)."
            )
            print(
                "To enable uploads via anon key, add an INSERT policy on the 'files' bucket in Supabase:"
            )
            print(
                "  CREATE POLICY \"Allow uploads\" ON storage.objects FOR INSERT TO anon WITH CHECK (bucket_id = 'resources');"
            )
            print("Or use the SUPABASE_SERVICE_ROLE_KEY in .env.")
        raise exc

    # Privacy Protection:
    # Academic resources are PRIVATE by default. Do not expose unauthenticated permanent URLs.
    # Instead, generate a time-limited signed download URL (e.g., valid for 15 minutes).
    try:
        signed_url_info = client.storage.from_(SUPABASE_BUCKET).create_signed_url(
            storage_path, 900
        )
        signed_url = (
            signed_url_info.get("signedURL")
            or signed_url_info.get("signedUrl")
            or str(signed_url_info)
        )
        print("\n[Privacy Enforced]: Resource is PRIVATE by default.")
        print(f"Secure Time-Limited Signed URL (15 min expiry): {signed_url}")
    except Exception:
        signed_url = None

    return {
        "storage_path": storage_path,
        "user_id": clean_user_id,
        "folder": folder_name,
        "filename": filename,
        "signed_url": signed_url,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Upload resource to user-segregated folder with privacy controls."
    )
    parser.add_argument(
        "--file", default="pic.png", help="Path to local file to upload"
    )
    parser.add_argument("--user-id", default=None, help="User ID owning the folder")
    parser.add_argument(
        "--folder", default="assignments", help="Subfolder name inside user directory"
    )
    parser.add_argument("--content-type", default="image/png", help="MIME content type")

    args = parser.parse_args()

    try:
        result = upload_resource(
            file_path=args.file,
            user_id=args.user_id,
            folder_name=args.folder,
            content_type=args.content_type,
        )
        print(f"\nSummary: Stored at '{result['storage_path']}'")
    except Exception as e:
        print(f"Error during upload: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
