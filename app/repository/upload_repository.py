from app.repository.db import supabase
import logging
from uuid import UUID
from storage3.exceptions import StorageApiError


logging.basicConfig(level=logging.INFO)
'''
Strictly will only receive mp4 files. Any other file type will have to transform to mp4 before uploading to supabase bucket.
'''

async def save_to_bucket(content: bytes, file_name: str) -> str:
    path = f"uploads/{file_name}"
    storage = supabase.storage.from_("videos")
    url = storage.get_public_url(path)

    try:
        storage.upload(
            path,
            content,
            {"content-type": "video/mp4"}
        )
    except StorageApiError as error:
        if error.status == "409" and error.code == "Duplicate":
            logging.info(f"File {file_name} already exists. Returning existing URL.")
            logging.info(f"Existing URL for {file_name}: {url}")
            return url

        logging.error(f"Error uploading {file_name}: {error}")
        raise
    
    return url



async def save_to_database(file_url: str, ticket_id: UUID) -> None:
    try:
        response = supabase.table("ticket").update({"url": file_url}).eq("ticket_id", str(ticket_id)).execute()
        if not response: 
            logging.error(f"Error updating database for ticket_id {ticket_id}: {response.data}")
            raise Exception(f"Database update failed for ticket_id {ticket_id}")
        return
    except Exception as e:
        logging.error(f"Error updating database for ticket_id {ticket_id}: {e}")
        raise


async def create_ticket(officer, plate_number, location, video_url):
    pass