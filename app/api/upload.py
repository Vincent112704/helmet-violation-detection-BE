from fastapi import APIRouter, Depends
from app.dependencies.auth import get_user

router = APIRouter()

@router.get('/upload-test')
async def test(user=Depends(get_user)):
    return {'message': 'upload test success'}