from app.repository.db import supabase
import logging
from uuid import UUID
from storage3.exceptions import StorageApiError


logging.basicConfig(level=logging.INFO)
'''
Strictly will only receive mp4 files. Any other file type will have to transform to mp4 before uploading to supabase bucket.
'''

from typing import TypedDict


class TicketInput(TypedDict):
    officer: UUID
    plate_number: str
    location: str
    video_url: str

    

async def save_to_bucket(content: bytes, file_name: str) -> str:
    path = f"uploads/{file_name}"
    storage = supabase.storage.from_("videos")
    url = get_storage_url(file_name)

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

def get_storage_url(file_name: str) -> str:
    path = f"uploads/{file_name}"
    storage = supabase.storage.from_("videos")
    url = storage.get_public_url(path)

    return url

'''
    Commented out save_to_database() because it is no longer needed
    Initially I created it so that I can update the ticket table's url column after video url is already available 
    but I learned that you can just pre-construct the url and use the same url to save the video
    basically url is now created before video has been uploaded
'''

# async def save_to_database(file_url: str, ticket_id: UUID) -> None:
#     try:
#         response = supabase.table("ticket").update({"url": file_url}).eq("ticket_id", str(ticket_id)).execute()
#         if not response: 
#             logging.error(f"Error updating database for ticket_id {ticket_id}: {response.data}")
#             raise Exception(f"Database update failed for ticket_id {ticket_id}")
#         return
#     except Exception as e:
#         logging.error(f"Error updating database for ticket_id {ticket_id}: {e}")
#         raise



async def create_tickets(tickets: list[TicketInput]):
    """
    Insert one or more ticket records into the `tickets` table in a single
    atomic operation — either all rows are inserted, or none are (a single
    INSERT statement is one transaction in Postgres).

    Args:
        tickets: list of ticket dicts, each with officer, plate_number,
                 location, and video_url.

    Returns:
        list of created rows on success.
    Raises:
        ValueError if `tickets` is empty.
        RuntimeError on failure or if no data is returned.
    """
    if not tickets:
        raise ValueError("tickets must contain at least one entry")

    rows = [
        {
            "officer": str(t["officer"]),
            "plate_number": t["plate_number"],
            "location": t["location"],
            "url": t["video_url"],
        }
        for t in tickets
    ]

    try:
        response = supabase.table("ticket").insert(rows).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to create ticket(s): {e}") from e

    if not response.data:
        raise RuntimeError("Ticket creation returned no data")

    return response.data