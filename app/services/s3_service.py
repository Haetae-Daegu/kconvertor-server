import boto3
import os
from werkzeug.utils import secure_filename
from typing import List
from app.services.storage_interface import StorageInterface
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv
from pathlib import Path


class S3Service(StorageInterface):
    def __init__(self):
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("SPACE_ENDPOINT"),
            aws_access_key_id=os.environ.get("SPACE_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("SPACE_SECRET_KEY"),
            region_name=os.environ.get("SPACE_REGION"),
        )
        self.space_name = os.environ.get("SPACE_NAME")

    def upload_files(
        self, files: List[FileStorage], folder: str = "accommodations"
    ) -> List[str]:
        image_urls = []

        for file in files:
            if file and file.filename:
                try:
                    file.seek(0)
                    filename = secure_filename(file.filename)
                    folder = folder.strip("/").rstrip("/")
                    if folder == self.space_name:
                        s3_path = filename
                    else:
                        s3_path = f"{folder}/{filename}"

                    print(f"Uploading file to: {s3_path}")

                    self.s3_client.upload_fileobj(
                        file,
                        self.space_name,
                        s3_path,
                        ExtraArgs={
                            "ACL": "public-read",
                            "ContentType": file.content_type,
                        },
                    )
                    image_url = f"https://{self.space_name}.lon1.cdn.digitaloceanspaces.com/{folder}/{s3_path}"
                    image_urls.append(image_url)

                except Exception as e:
                    print(f"Error uploading file {file.filename}: {str(e)}")
                    continue
                finally:
                    file.close()

        return image_urls

    def delete_file(self, file_url: str) -> bool:
        try:
            path = file_url.split(
                f"{self.space_name}.{os.getenv('SPACE_REGION')}.digitaloceanspaces.com/"
            )[1]
            self.s3_client.delete_object(Bucket=self.space_name, Key=path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_url}: {e}")
            return False
