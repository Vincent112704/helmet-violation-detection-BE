from app.repository.upload_repository import save_to_bucket, save_to_database
from ultralytics import YOLO

'''
did try except in the repo layer so when there is exception it propagates to service
still thinking about how to handle the exception (retry logic, how client knows if the upload failed, etc)
#TODO:
    - Test object Upload Repo
    - Test url update Repo
    - Integrate YOLO model to
    - add association logic for ticket violation detection
    - add logic for OCR model
'''


async def process_uploaded_file(content: bytes, file_name: str):
    pass