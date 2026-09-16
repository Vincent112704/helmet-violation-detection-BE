from app.repository.upload_repository import save_to_bucket, save_to_database
from ultralytics import YOLO
from app.repository.upload_repository import save_to_bucket, save_to_database
import cv2
import tempfile
import logging

logging.basicConfig(level=logging.INFO)

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


async def process_uploaded_file(content: bytes, file_name: str, model):
    detections = []
    logging.info(f"Processing file: {file_name}")
    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        temp_file.write(content)
        temp_file.flush()

        cap = cv2.VideoCapture(temp_file.name)

        while True:
            success, frame = cap.read()

            if not success:
                break

            results = model(frame)
            detections.append(results)

        cap.release()

    logging.info(f"Detections: {detections}")
    return detections


async def associate_ticket_with_violation(ticket_id: str, violation_type: str):
    # Implement the logic to associate the ticket with the detected violation
    pass

async def perform_ocr_on_video(video_path: str):
    # Implement the logic to perform OCR on the video and extract plate number when yolo association logic detects a violation
    pass


async def save_violation_to_supabase(ticket_id: str, violation_type: str, plate_number: str):
    # Implement the logic to save the violation details to the database
    # Just thought about it but there should be two seperate logic for saving to DB one for creating a row and one for updating the row with the violation details
    pass

