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
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    def upload_files(self, files: List[FileStorage], folder: str = 'accommodations') -> List[str]:
        image_urls = []
        
        for file in files:
            if file and file.filename:
                try:
                    file.seek(0)
                    
                    file_content = file.read()                    
                    file.seek(0)
                    
                    filename = secure_filename(file.filename)
                    s3_path = f'{folder}/{filename}'
                    
                    try:
                        self.s3_client.put_object(
                            Bucket=self.bucket_name,
                            Key=s3_path,
                            Body=file_content,
                            ContentType=file.content_type
                        )
                        
                        image_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_path}"
                        image_urls.append(image_url)
                        print(f"Successfully uploaded {filename} to S3")
                        
                    except Exception as upload_error:
                        raise upload_error
                        
                except Exception as e:
                    continue
                finally:
                    file.close()
                
        return image_urls

    def delete_file(self, file_url: str) -> bool:
        try:
            path = file_url.split(f"{self.bucket_name}.s3.amazonaws.com/")[1]
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_url}: {e}")
            return False 