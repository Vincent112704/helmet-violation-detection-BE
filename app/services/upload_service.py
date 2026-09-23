from app.repository.upload_repository import save_to_bucket, save_to_database, create_ticket
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


async def yolo_detection(content: bytes, file_name: str, model, location: str):
    
    logging.info(f"Processing file: {file_name}")
    video_path = save_to_bucket(content, file_name)

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
                    last_results = results

                # Draw the latest detections
                if last_results is not None:
                    frame = draw_detections(
                        frame,
                        last_results,
                        model,
                    )

                await associate_ticket_with_violation(last_results, model, video_path)

                out.write(frame)

                frame_counter += 1

        finally:
            #should add logic here to save the annotated video to the bucket and update the url in the database
            cap.release()
            out.release()


    


async def associate_ticket_with_violation(results, model, video_path: str):
    result = results[0]
    tracked_plates = set()  # To keep track of already processed plate numbers

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
                # call ocr model and pass plate number bounding box to extract the plate number
                # plate_number_text = await perform_ocr_on_video(plate_number)
                # if plate_number_text in tracked_plates:
                #     continue  # Skip if this plate number has already been processed
                # tracked_plates.add(plate_number)
                #Create violation record with plate number as plate_number_text
                pass
            
    #after person loop ends insert all plate number in set

         
            
async def perform_ocr_on_video(plate_box):
    # Implement the logic to perform OCR on the video and extract plate number when yolo association logic detects a violation
    pass


async def save_violation_to_supabase(ticket_id: str, violation_type: str, plate_number: str):
    # Implement the logic to save the violation details to the database
    # Just thought about it but there should be two seperate logic for saving to DB one for creating a row and one for updating the row with the violation details
    pass

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
