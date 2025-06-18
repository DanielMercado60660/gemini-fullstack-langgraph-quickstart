from __future__ import annotations

import os

from google.cloud import secretmanager

def get_secret(project_id: str, secret_id: str, version_id: str = "latest") -> str | None:
    """
    Accesses a secret version from Google Cloud Secret Manager.

    Args:
        project_id: The Google Cloud project ID.
        secret_id: The ID of the secret.
        version_id: The version of the secret (defaults to "latest").

    Returns:
        The secret payload as a string, or None if an error occurs.
    """
    if not project_id:
        print("Error: GCP_PROJECT_ID is not set.")
        return None
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_id} in project {project_id}: {e}")
        return None
