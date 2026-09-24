from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from app.dependencies.auth import get_user
from app.services.upload_service import yolo_detection
from fastapi import Request
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()

    
@router.post('/')
async def upload_file(request: Request, background_tasks: BackgroundTasks, video_file: UploadFile = File(...), user = Depends(get_user)):
    content = await video_file.read()
    form = await request.form()
    location = form.get('location', '')
    file_name = video_file.filename
    officer = user.id
    yolo_model = request.app.state.model
    ocr_model = request.app.state.ocr_model
    try: 
        length_mb = len(content) / (1024 * 1024)
        if length_mb > 50:
            raise ValueError("File size exceeds 50 MB limit.")
        
        background_tasks.add_task(yolo_detection, content, file_name, yolo_model, location, officer, ocr_model)
        return {"message": "File queued for processing."}
    except Exception as e:
        return {"error": str(e)}

    
