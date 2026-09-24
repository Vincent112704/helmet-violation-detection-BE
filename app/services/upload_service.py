from app.repository.upload_repository import save_to_bucket, create_tickets, get_storage_url
import cv2
import tempfile
import logging
from uuid import UUID
import os
from paddleocr import PaddleOCR
import asyncio
from ultralytics import YOLO
logging.basicConfig(level=logging.INFO)



FRAME_INTERVAL = 8 #Configurable frame interval for YOLO detection, currently set to process every 8th frame

'''

#TODO: as of Sept. 23, 2026
    - Will need to pass auth token of logged in officer to use it as FK in ticket table
    - Create a logic for inserting all tracked plates at once (push all tracked plates once so program does not have to insert back and forth)
'''


async def yolo_detection(content: bytes, file_name: str, model: YOLO, location: str, officer: UUID, ocr_model: PaddleOCR):
    
    logging.info(f"Processing file: {file_name}")
    
    video_path = get_storage_url(file_name) # nothing has been saved yet url of video is pre made

    with tempfile.NamedTemporaryFile(suffix=".mp4") as temp_file:
        temp_file.write(content)
        temp_file.flush()

        cap = cv2.VideoCapture(temp_file.name)

        # Create output video
        output_path = f"/app/{file_name}_detected.mp4" # simply be used to read annotated video
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
                    last_results = results

                # Draw the latest detections
                if last_results is not None:
                    frame = draw_detections(
                        frame,
                        last_results,
                        model,
                    )

                await associate_ticket_with_violation(last_results, model, video_path, location, officer, ocr_model)

                out.write(frame)

                frame_counter += 1

        finally:
            
            cap.release()
            out.release()

            with open(output_path, 'rb') as f:
                annotated_bytes = f.read()

            save_to_bucket(annotated_bytes, file_name)

            if os.path.exists(output_path):
                os.remove(output_path)
            


async def associate_ticket_with_violation(results, model: YOLO, video_path: str, location: str, officer: UUID, ocr_model: PaddleOCR):
    result = results[0]
    tracked_plates = set()  # To keep track of already processed plate numbers
    violations = []

    helmets = get_boxes_by_class(result, model, "Helmet")
    persons = get_boxes_by_class(result, model, "Person")
    motorcycles = get_boxes_by_class(result, model, "Motorcycle")
    plates = get_boxes_by_class(result, model, "Plate_number")

    for person in persons:
        motorcycle = find_associated_motorcycle(person, motorcycles)

        if motorcycle is None:
            continue

        helmet = find_associated_helmet(person, helmets)

        if helmet is None:
            # Violation detected: Person on motorcycle without helmet
            # Find associated plate number for the motorcycle
            plate_number = find_associated_plate(motorcycle, plates)
            if plate_number is None:
                logging.info("No plate number detected for the motorcycle.")
            else:
                
                plate_number_text = await perform_ocr_on_video(plate_number, result.orig_img, ocr_model)
                if plate_number_text in tracked_plates:
                    continue 

                tracked_plates.add(plate_number)
                violations.append({
                    "officer": officer,
                    "plate_number": plate_number_text,
                    "location": location,
                    "video_url": video_path,
                })

    if not violations:
        logging.info("No violations detected in this frame/video.")
        return []

    created_tickets = await create_tickets(violations)
    logging.info(f"Created {len(created_tickets)} ticket(s) for detected violations.")

    return created_tickets
                
                
async def perform_ocr_on_video(plate_box, frame, ocr_model: PaddleOCR):
    if frame is None or plate_box is None:
        return None

    try:
        x1, y1, x2, y2 = map(int, plate_box[:4])
    except (TypeError, ValueError):
        x1, y1, x2, y2 = map(int, plate_box.xyxy[0])

    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return None

    margin = 5
    plate_crop = frame[
        max(0, y1 - margin):min(h, y2 + margin),
        max(0, x1 - margin):min(w, x2 + margin),
    ]
    if plate_crop.size == 0:
        return None

    plate_crop = _preprocess_plate(plate_crop)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ocr_model.predict, plate_crop)

    return _extract_best_text(result)


def _preprocess_plate(crop):
    h, w = crop.shape[:2]
    min_height = 64
    if h < min_height:
        scale = min_height / h
        crop = cv2.resize(
            crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC
        )
    crop = cv2.fastNlMeansDenoisingColored(crop, None, 10, 10, 7, 21)
    lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _extract_best_text(result, min_confidence=0.5):
    """
    PaddleOCR 3.x `.predict()` returns a list of Result objects.
    Each is dict-like with 'rec_texts', 'rec_scores', 'rec_polys'.
    """
    if not result:
        return None

    res = result[0]

    texts = res.get("rec_texts") or []
    scores = res.get("rec_scores") or []
    polys = res.get("rec_polys")

    if not texts:
        return None

    lines = []
    for i, (text, score) in enumerate(zip(texts, scores)):
        if score >= min_confidence and text.strip():
            left_x = float(polys[i][:, 0].min()) if polys is not None else i
            lines.append((left_x, text.strip()))

    if not lines:
        return None

    lines.sort(key=lambda t: t[0])
    plate_text = "".join(text for _, text in lines)
    plate_text = "".join(c for c in plate_text.upper() if c.isalnum())

    return plate_text or None



def create_video_writer(output_path: str, cap: cv2.VideoCapture):
    '''
    Creates a VideoWriter object to write the output video with the same properties as the input video.
    Args:
        output_path: The path where the output video will be saved.
        cap: The VideoCapture object for the input video.
    
    Returns:
        A VideoWriter object to write the output frame.
    '''
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
    '''
    Draws bounding boxes and labels on the frame based on YOLO detection results.
    Args:
        frame: The video frame to draw on.
        results: The YOLO detection results.
        model: The YOLO model used for detection (to get class names).
    
    Returns:
        frame: The frame with drawn bounding boxes and labels.
    
    '''
    result = results[0]
    print("--------------------")
    print(f"{result}.")
    print("--------------------")

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

def get_boxes_by_class(result, model, class_name):
    '''
    Returns a list of bounding boxes specified by the arguments passed

    Args:
        result: Yolo model's last frame results
        model: YOLO model to extract the class_id
        class_name: Class name of a specific class

    returns:
        boxes: a list of bounding boxes of a specific class
    '''
    boxes = []

    for box in result.boxes:
        class_id = int(box.cls[0])

        if model.names[class_id] == class_name:
            boxes.append(box.xyxy[0].tolist())

    return boxes

def find_associated_motorcycle(person_box, motorcycles):
    '''
    Finds the associated motorcycle for a given person box based on bounding box overlap.
    Using the formula: 
        person_motor_overlap = area(Person ∩ Motorcycle) / area(Person) 
        if person_motor_overlap > THRESHOLD, then we can say the person is associated with the motorcycle

    Args:
        person_box: The bounding box of the person (x1, y1, x2, y2).
        motorcycles: A list of bounding boxes for detected motorcycles.

    Returns:
        motorcycle_box: The bounding box of the associated motorcycle if found 
        None: No association

    '''
    THRESHOLD = 0.5  # Define a threshold for association
    px1, py1, px2, py2 = person_box
    person_box_area = (px2 - px1) * (py2 - py1) # Get the area of person box

    for motorcycle_box in motorcycles:
        mx1, my1, mx2, my2 = motorcycle_box
        # calculate the intersection area of person_box_area and motorcycle_box_area
        # Intersection rectangle
        ix1 = max(px1, mx1) # The leftmost x-coordinate of the intersection rectangle
        iy1 = max(py1, my1) # The topmost y-coordinate of the intersection rectangle
        ix2 = min(px2, mx2) # The rightmost x-coordinate of the intersection rectangle
        iy2 = min(py2, my2) # The bottommost y-coordinate of the intersection rectangle

        if ix1 >= ix2 or iy1 >= iy2:
            continue  # No intersection


        intersection_area = (ix2 - ix1) * (iy2 - iy1)

        # Calculate the overlap ratio
        overlap = intersection_area / person_box_area

        if overlap > THRESHOLD:
            return motorcycle_box  # Return the associated motorcycle box

    return None
        

def find_associated_helmet(person_box, helmets):
    '''
    Used containment logic to associate person with helmet
    Basically if bounding box of helmet is completely inside person then helmet belongs to person

    Args: 
        person_box: bounding box of person
        helmets: a list of helmet bounding boxes
    
    Returns:
        helmet_box: bounding box of helmet
        None: No association
    
    '''
    px1, py1, px2, py2 = person_box

    for helmet_box in helmets:
        hx1, hy1, hx2, hy2 = helmet_box

        if hx1 >= px1 and hy1 >= py1 and hx2 <= px2 and hy2 <= py2:
            return helmet_box  

    return None

def find_associated_plate(motorcycle_box, plates):
    '''
    Used containment logic to associate motorcycle with plate number
    Basically if bounding box of plate number is completely inside motorcycle then plate number belongs to motorcycle

    Args:
        motorcycle_box: bounding box of motorcycle
        plates: list of plate number bounding box

    Returns:
        plate_box: bounding box of plate number
        None: No association
    '''
    mx1, my1, mx2, my2 = motorcycle_box

    for plate_box in plates:
        px1, py1, px2, py2 = plate_box

        if px1 >= mx1 and py1 >= my1 and px2 <= mx2 and py2 <= my2:
            return plate_box

    return None
