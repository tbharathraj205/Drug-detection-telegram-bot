import os
import logging
from telethon import TelegramClient, functions
from telethon.tl.functions.contacts import SearchRequest
from telethon.tl.functions.messages import GetHistoryRequest, ImportChatInviteRequest
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto
from telethon.errors import ChatAdminRequiredError, InviteHashInvalidError, InviteHashExpiredError

# --- Configuration ---
# !! Replace with your own values from my.telegram.org !!
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
phone_number = 'YOUR_PHONE_NUMBER' # Use international format (e.g., +12223334444)
session_name = 'sess001'
# --- End Configuration ---

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keywords
drug_keywords = [
    'weed', 'cocaine', 'LSD', 'meth', 'heroin', 'ecstasy', 'MDMA',
    'marijuana', 'crystal', 'shrooms', 'acid', 'opioids', 'crack'
]

groupsdict = {}

# Initialize the Telegram client
client = TelegramClient(session_name, api_id, api_hash)

async def search_drug_groups():
    found_groups = []

    for keyword in drug_keywords:
        result = await client(SearchRequest(
            q=keyword,
            limit=10  # Adjust as needed
        ))

        for chat in result.chats:
            if chat.megagroup:  # Checks if it's a group
                group_info = {
                    'title': chat.title,
                    'id': chat.id,
                    'type': 'Group'
                }
                found_groups.append(group_info)
                groupsdict[chat.title] = group_info

            elif chat.broadcast:  # Check if it's a channel
                channel_info = {
                    'title': chat.title,
                    'id': chat.id,
                    'type': 'Channel'
                }
                found_groups.append(channel_info)
                groupsdict[chat.title] = channel_info

            print(f"Found {chat.title} with ID: {chat.id}")

    return found_groups

async def join_channel_or_group(group_info):
    try:
        if group_info['type'] == 'Channel':
            await client(functions.channels.JoinChannelRequest(
                channel=group_info['id']
            ))
            logger.info(f"Successfully joined Channel: {group_info['title']}")

        elif group_info['type'] == 'Group':
            # Note: Joining groups by ID like this might not work.
            # You usually need an invite hash (e.g., 'https://t.me/joinchat/HASH')
            # Using ImportChatInviteRequest with just a group ID will likely fail.
            # This part of the logic might need revision.
            await client(ImportChatInviteRequest(
                hash=group_info['id'] # This is likely incorrect, needs an invite hash
            ))
            logger.info(f"Successfully joined Group: {group_info['title']}")

    except Exception as e:
        logger.error(f"Failed to join {group_info['type']}: {group_info['title']} - {e}")

async def fetch_admin_info(group_info):
    try:
        admins = await client(functions.channels.GetParticipantsRequest(
            channel=group_info['id'],
            filter=functions.channels.ChannelParticipantsAdmins(),
            offset=0,
            limit=100,
            hash=0
        ))

        admin_info = []
        for admin in admins.participants:
            try:
                # Check if the user has admin rights
                if hasattr(admin, 'admin_rights') and admin.admin_rights:
                    admin_info.append({
                        'id': admin.id,
                        'username': admin.username or 'No username',
                        'admin_rights': admin.admin_rights
                    })
                    print(f"Admin: {admin.first_name}, Admin Rights: {admin.admin_rights}")
                else:
                    # Handle case where the user is not an admin
                    print(f"User {admin.first_name} is not an admin.")
            except AttributeError as e:
                print(f"Error while accessing admin rights for user {admin.first_name}: {str(e)}")
        
        return admin_info
    except Exception as e:
        logger.error(f"Error fetching admin details for {group_info['title']}: {e}")
        return []

async def fetch_and_process_messages(group_info, limit=100):
    try:
        # Fetch message history with the specified limit
        group = await client.get_entity(group_info['id'])
        history = await client(GetHistoryRequest(
            peer=group,
            limit=limit,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        # Fetch admin details
        admins = await fetch_admin_info(group_info)

        # Process the fetched messages
        return await process_messages(group_info, history.messages, admins)
    except ChatAdminRequiredError:
        logger.error(f"Cannot access group {group_info['title']}: Admin rights required.")
    except Exception as e:
        logger.error(f"An error occurred while fetching messages from {group_info['title']}: {e}")

async def process_messages(group_info, messages, admins):
    # Create directories for saving files if they don't exist
    os.makedirs(f'photos/{group_info["title"]}', exist_ok=True)
    os.makedirs(f'videos/{group_info["title"]}', exist_ok=True)
    os.makedirs(f'texts/{group_info["title"]}', exist_ok=True)
    os.makedirs(f'documents/{group_info["title"]}', exist_ok=True) # Added documents directory

    # Create a text file for this group or channel
    text_file_path = f'texts/{group_info["title"]}/{group_info["title"]}_messages.txt'
    
    with open(text_file_path, 'w', encoding='utf-8') as text_file:
        # Write group/channel details
        text_file.write(f"Group/Channel Name: {group_info['title']}\n")
        text_file.write(f"ID: {group_info['id']}\n")
        
        # Write admin details
        text_file.write("\nAdmins:\n")
        for admin in admins:
            text_file.write(f"Admin ID: {admin['id']}, Username: {admin['username']}, Admin Rights: {admin.get('admin_rights')}\n")
        text_file.write("\nMessages:\n\n")
        
        for message in messages:
            try:
                # Write text messages
                if message.message:
                    text_file.write(f"Message {message.id}: {message.message}\n\n")
                    print(f"Text saved in: {text_file_path}")

                # Save photos
                if isinstance(message.media, MessageMediaPhoto):
                    photo_filename = f'photos/{group_info["title"]}/photo_{message.id}.jpg'
                    await client.download_media(message, file=photo_filename)
                    text_file.write(f"Photo saved: {photo_filename}\n")
                    print(f"Photo saved: {photo_filename}")

                # Save videos or other documents
                if isinstance(message.media, MessageMediaDocument):
                    mime_type = message.media.document.mime_type
                    # Check if the document is a video
                    if mime_type and mime_type.startswith('video/'):
                        video_filename = f'videos/{group_info["title"]}/video_{message.id}.mp4'
                        await client.download_media(message, file=video_filename)
                        text_file.write(f"Video saved: {video_filename}\n")
                        print(f"Video saved: {video_filename}")
                    else:
                        # Handle other document types
                        # Try to get original file name extension
                        ext = '.dat' # default extension
                        for attr in message.media.document.attributes:
                            if hasattr(attr, 'file_name'):
                                ext = os.path.splitext(attr.file_name)[-1]
                                break
                        
                        document_filename = f'documents/{group_info["title"]}/document_{message.id}{ext}'
                        await client.download_media(message, file=document_filename)
                        text_file.write(f"Document saved: {document_filename}\n")
                        print(f"Document saved: {document_filename}")

            except Exception as e:
                print(f"Failed to process message {message.id}: {e}")

async def main():
    await client.start(phone=phone_number)

    # Step 1: Search for groups and channels related to drug trafficking
    groups = await search_drug_groups()

    # Step 2: Save the found groups and channels to a file
    with open