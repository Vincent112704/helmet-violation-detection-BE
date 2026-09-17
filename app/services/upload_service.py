from app.repository.upload_repository import save_to_bucket, save_to_database
from ultralytics import YOLO
from app.repository.upload_repository import save_to_bucket, save_to_database
import cv2
import tempfile
import logging

logging.basicConfig(level=logging.INFO)



FRAME_INTERVAL = 8 #Configurable frame interval for YOLO detection, currently set to process every 8th frame

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


async def yolo_detection(content: bytes, file_name: str, model):
    detections = []

    logging.info(f"Processing file: {file_name}")

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        temp_file.write(content)
        temp_file.flush()

        cap = cv2.VideoCapture(temp_file.name)

        # Create output video
        output_path = f"/app/{file_name}_detected.mp4"
        out = create_video_writer(output_path, cap)

        frame_counter = 0
        last_results = None

        try:
            while True:
                success, frame = cap.read()

                if not success:
                    break

                if frame_counter % FRAME_INTERVAL == 0:
                    results = model(frame)

                    detections.append(results)
                    last_results = results

                # Draw the latest detections
                if last_results is not None:
                    frame = draw_detections(
                        frame,
                        last_results,
                        model,
                    )

                out.write(frame)

                frame_counter += 1

        finally:
            cap.release()
            out.release()

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

def create_video_writer(output_path: str, cap: cv2.VideoCapture):
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    return cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (width, height),
    )


def draw_detections(frame, results, model):
    result = results[0]

    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])

        class_name = model.names[class_id]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        cv2.putText(
            frame,
            f"{class_name} {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    return frame

