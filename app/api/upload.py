from fastapi import APIRouter

router = APIRouter()

@router.get('/upload-test')
async def test():
    return {'message': 'upload test success'}