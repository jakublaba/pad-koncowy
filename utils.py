import os
import sys

import dotenv
from azure.storage.blob import BlobServiceClient, ContainerClient, BlobClient

dotenv.load_dotenv()
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONN_STRING")


def get_blob_service_client() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)


def get_container_client(blob_service_client: BlobServiceClient, container_name: str) -> ContainerClient:
    return blob_service_client.get_container_client(container_name)


def get_blob_client(container_client: ContainerClient, blob_name: str) -> BlobClient:
    return container_client.get_blob_client(blob_name)


def download_all_csvs(container: str, dir: str) -> None:
    blob_service_client = get_blob_service_client()
    container_client = get_container_client(blob_service_client, container)
    if not os.path.exists(dir):
        print(f"{dir} didn't exist, creating it", file=sys.stderr)
        os.makedirs(dir)
    for blob in container_client.list_blobs():
        if blob.name.endswith(".csv"):
            local_path = os.path.join(dir, blob.name)

            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            print(f"Downloading {dir}/{blob.name}", file=sys.stderr)
            with open(local_path, "wb") as file:
                blob_client = container_client.get_blob_client(blob)
                file.write(blob_client.download_blob().readall())
