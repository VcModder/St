import os
import tempfile
from datetime import datetime, timedelta, timezone

from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.errors import RPCError

from nsfw import is_nsfw


API_ID = int(os.getenv("24984010", "0"))
API_HASH = os.getenv("dbcf69134629b947fbbf0544860a6a74", "")
BOT_TOKEN = os.getenv("8855777009:AAF75aXE8yogImBS_4TrEkP6GEjfCqsAHr0", "")

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError(
        "API_ID, API_HASH aur BOT_TOKEN set karo."
    )


app = Client(
    "nsfw_moderation_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# Har group me user ke warnings alag rahenge
warnings = {}

MAX_WARNINGS = 3


@app.on_message(filters.sticker & filters.group)
async def sticker_moderation(client: Client, message: Message):

    # User information nahi hai to ignore
    if not message.from_user:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Admin/Owner ke stickers scan nahi karenge
    try:
        member = await client.get_chat_member(
            chat_id,
            user_id
        )

        if member.status in ("administrator", "owner"):
            return

    except Exception:
        pass


    # Abhi sirf normal/static stickers
    if message.sticker.is_animated or message.sticker.is_video:
        return


    path = None

    try:

        # Sticker download
        with tempfile.NamedTemporaryFile(
            suffix=".webp",
            delete=False
        ) as temp:
            path = temp.name


        await client.download_media(
            message,
            file_name=path
        )


        # Hugging Face se NSFW check
        detected = is_nsfw(path)


        if not detected:
            return


        # NSFW sticker delete
        try:
            await message.delete()
        except RPCError as e:
            print("Delete error:", e)


        # Warning count
        key = (chat_id, user_id)

        warnings[key] = warnings.get(key, 0) + 1

        count = warnings[key]

        user = message.from_user


        # 3 warnings = 24 hour mute
        if count >= MAX_WARNINGS:

            try:

                until = (
                    datetime.now(timezone.utc)
                    + timedelta(hours=24)
                )

                await client.restrict_chat_member(
                    chat_id,
                    user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False
                    ),
                    until_date=until
                )


                await client.send_message(
                    chat_id,
                    f"🔇 {user.mention} muted for 24 hours.\n\n"
                    f"Reason: 3 NSFW sticker warnings."
                )

            except RPCError as e:

                print("Mute error:", e)


        else:

            await client.send_message(
                chat_id,
                f"⚠️ {user.mention}, NSFW sticker allowed nahi hai.\n\n"
                f"Warning: {count}/{MAX_WARNINGS}"
            )


    except Exception as e:

        print("Moderation error:", e)


    finally:

        # Temporary image delete
        if path and os.path.exists(path):

            try:
                os.remove(path)
            except OSError:
                pass


print("🤖 NSFW Moderation Bot started...")

app.run()
