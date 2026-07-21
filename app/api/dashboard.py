from fastapi import APIRouter

router = APIRouter()

@router.get('/dashboard-test')
async def test():
    return { "message": "dashboard test success"}