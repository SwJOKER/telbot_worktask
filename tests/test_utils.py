import datetime

import datetime
from aiogram.types import User, Chat, Message, CallbackQuery, Update
import datetime

TEST_USER = User(
    id=133191215,
    is_bot=False,
    first_name='Testing',
    last_name='User',
    username='PyTest',
    language_code='ru-Ru',
    is_premium=False,
    added_to_attachment_menu=False,
    can_join_groups=False,
    can_read_all_group_messages=None,
    supports_inline_queries=None)

TEST_CHAT = Chat(
    id = 209,
    type = 'private',
    title = None,
    username = TEST_USER.username,
    first_name= TEST_USER.first_name,
    last_name = TEST_USER.last_name,
    photo = None,
    bio = None,
    has_private_forwards = False,
    has_restricted_voice_and_video_messages = True,
    join_to_send_messages = True,
    join_by_request = None,
    description = None,
    invite_link = None,
    pinned_message = None,
    permissions = None,
    slow_mode_delay = None,
    message_auto_delete_time= None,
    has_protected_content = None,
    sticker_set_name = None,
    can_set_sticker_set = None,
    linked_chat_id = None,
    location = None
)

def get_message(text: str):
    return Message(from_user=TEST_USER,
                      message_id = 1,
                      date = str(datetime.datetime.now().timestamp()),
                      chat = TEST_CHAT,
                      text = text,
                    )

def get_update(message: Message, callback: CallbackQuery = None):
    return Update(
        update_id = 26,
        message = message)



