from fastapi import APIRouter, Depends, UploadFile, File
from app.dependencies.auth import get_user

router = APIRouter()

# @router.get('/upload-test')
# async def test(user=Depends(get_user)):
#     return {'message': 'upload test success'}

@router.post('/')
async def upload_file(video_file: UploadFile = File(...)): #remove auth temporarily for testing
    content = await video_file.read()

    print(len(content))
    print(video_file.filename)
    return {'message': 'upload file success'}