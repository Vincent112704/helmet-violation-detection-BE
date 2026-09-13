

'''
did try except in the repo layer so when there is exception it propagates to service
still thinking about how to handle the exception (retry logic, how client knows if the upload failed, etc)
'''
async def process_uploaded_file(content: bytes, file_name: str):
    pass