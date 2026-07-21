from fastapi import APIRouter

router = APIRouter()


@router.get('/table-test')
async def test():
    return {'message': 'table test success'}
