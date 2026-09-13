from app.repository.db import supabase
import logging
from uuid import UUID
logging.basicConfig(level=logging.INFO)
'''
Strictly will only receive mp4 files. Any other file type will have to transform to mp4 before uploading to supabase bucket.
'''

async def save_to_bucket(content: bytes, file_name: str):
    path = f"uploads/{file_name}"
    try: 
        supabase.storage.from_('videos').upload(
            path,
            content,
            {"content-type": "video/mp4"}
        )

        url = supabase.storage.from_('videos').get_public_url(path)

        return url
    except Exception as e:
        logging.error(f"Error uploading {file_name} to Supabase bucket: {e}")
        raise



async def save_to_database(file_url: str, ticket_id: UUID):
    try:
        response = supabase.table("ticket").update({"url": file_url}).eq("ticket_id", str(ticket_id)).execute()
        if response.status_code != 200:
            logging.error(f"Error updating database for ticket_id {ticket_id}: {response.data}")
            raise Exception(f"Database update failed for ticket_id {ticket_id}")
        return True
    except Exception as e:
        logging.error(f"Error updating database for ticket_id {ticket_id}: {e}")
        raise