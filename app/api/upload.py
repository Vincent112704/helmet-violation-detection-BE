from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from app.dependencies.auth import get_user
from app.services.upload_service import yolo_detection
from app.repository.upload_repository import save_to_bucket, save_to_database
from fastapi import Request



router = APIRouter()

# # @router.post('/upload-test')
# async def test(video_file: UploadFile = File(...)):
#     '''
#         object upload test to supabase bucket and update url to database
#         ticket_id is hardcoded for testing purposes
#         ticket_id = 1663ad13-0681-4ae4-8784-3b34aa085b55
#     '''

#     content = await video_file.read()
#     file_name = video_file.filename
#     try: 
#         length_mb = len(content) / (1024 * 1024)
#         if length_mb > 10:
#             raise ValueError("File size exceeds 10 MB limit.")
#         # url = await save_to_bucket(content, file_name)
#         # await save_to_database(url, "1663ad13-0681-4ae4-8784-3b34aa085b55")
#         return {"message": "File uploaded and database updated successfully."}
#     except Exception as e:
#         return {"error": str(e)}
    

@router.post('/')
async def upload_file(request: Request, background_tasks: BackgroundTasks, video_file: UploadFile = File(...)):
    content = await video_file.read()
    file_name = video_file.filename
    try: 
        length_mb = len(content) / (1024 * 1024)
        if length_mb > 50:
            raise ValueError("File size exceeds 50 MB limit.")
        
        background_tasks.add_task(yolo_detection, content, file_name, request.app.state.model)
        return {"message": "File queued for processing."}
    except Exception as e:
        return {"error": str(e)}

    
