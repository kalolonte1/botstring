import asyncio

from bot import bot, HU_APP
from pyromod import listen
from asyncio.exceptions import TimeoutError

from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded, FloodWait,
    PhoneNumberInvalid, ApiIdInvalid,
    PhoneCodeInvalid, PhoneCodeExpired
)

API_TEXT = """Hi, {}.
Saya Adalah Bot Untuk Mengambil String Pyrogram. Saya akan menghasilkan Sesi String dari Akun Telegram Anda.

By @knsgnwn

Sekarang kirim `API_ID` Anda yang sama dengan `APP_ID` untuk Memulai Sesi Pembuatan."""
HASH_TEXT = "Sekarang kirim `API_HASH` Anda.\n\nTekan /cancel untuk Membatalkan Tugas."
PHONE_NUMBER_TEXT = (
    "Sekarang kirim nomor Telepon akun Telegram Anda dalam Format Internasional. \n"
    "Termasuk kode negara. Contoh: **+628789101112**\n\n"
    "Tekan /cancel untuk Membatalkan Tugas."
)

@bot.on_message(filters.private & filters.command("start"))
async def genStr(_, msg: Message):
    chat = msg.chat
    api = await bot.ask(
        chat.id, API_TEXT.format(msg.from_user.mention)
    )
    if await is_cancel(msg, api.text):
        return
    try:
        check_api = int(api.text)
    except Exception:
        await msg.reply("`API_ID` Tidak Valid.\nTekan /start untuk Mulai lagi..")
        return
    api_id = api.text
    hash = await bot.ask(chat.id, HASH_TEXT)
    if await is_cancel(msg, hash.text):
        return
    if not len(hash.text) >= 30:
        await msg.reply("`APP_HASH` Tidak Valid.\nTekan /start untuk Mulai lagi.")
        return
    api_hash = hash.text
    while True:
        number = await bot.ask(chat.id, PHONE_NUMBER_TEXT)
        if not number.text:
            continue
        if await is_cancel(msg, number.text):
            return
        phone = number.text
        confirm = await bot.ask(chat.id, f'`Is "{phone}" benar? (y/n):` \n\nKirim: `y` (Jika Benar)\nKirim: `n` (Jika Salah)')
        if await is_cancel(msg, confirm.text):
            return
        if "y" in confirm.text:
            break
    try:
        client = Client("my_account", api_id=api_id, api_hash=api_hash)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`\nTekan /start Untuk Memulai Kembali.")
        return
    try:
        await client.connect()
    except ConnectionError:
        await client.disconnect()
        await client.connect()
    try:
        code = await client.send_code(phone)
        await asyncio.sleep(1)
    except FloodWait as e:
        await msg.reply(f"Anda memiliki Floodwait {e.x} Detik")
        return
    except ApiIdInvalid:
        await msg.reply("ID API dan Hash API Tidak Valid.\n\nTekan /start untuk Mulai lagi..")
        return
    except PhoneNumberInvalid:
        await msg.reply("Nomor Telepon Anda Tidak Valid.\n\nTekan /start untuk Mulai lagi.")
        return
    try:
        otp = await bot.ask(
            chat.id, ("OTP dikirim ke nomor telepon Anda, "
                      "Silakan masukkan OTP dalam format `1 2 3 4 5`. __(Spasi di antara setiap angka!)__ \n\n"
                      "Jika Bot tidak mengirimkan OTP maka coba /restart dan Mulai Tugas lagi dengan perintah /start ke Bot.\n"
                      "Tekan /cancel Untuk Membatalkan."), timeout=300)

    except TimeoutError:
        await msg.reply("Batas waktu tercapai 5 menit.\nTekan /start untuk Mulai lagi.")
        return
    if await is_cancel(msg, otp.text):
        return
    otp_code = otp.text
    try:
        await client.sign_in(phone, code.phone_code_hash, phone_code=' '.join(str(otp_code)))
    except PhoneCodeInvalid:
        await msg.reply("Kode Tidak Valid.\n\nTekan /start untuk Mulai lagi.")
        return
    except PhoneCodeExpired:
        await msg.reply("Kode Kedaluwarsa.\n\nTekan /start untuk Mulai lagi.")
        return
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                chat.id, 
                "Akun Anda memiliki Verifikasi Dua Langkah.\nSilakan masukkan Kata Sandi Anda.\n\nTekan /cancel untuk Membatalkan.",
                timeout=300
            )
        except TimeoutError:
            await msg.reply("`Time limit reached of 5 min.\n\nPress /start to Start again.`")
            return
        if await is_cancel(msg, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await client.check_password(new_code)
        except Exception as e:
            await msg.reply(f"**ERROR:** `{str(e)}`")
            return
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return
    try:
        session_string = await client.export_session_string()
        await client.send_message("me", f"#PYROGRAM #STRING_SESSION\n\n```{session_string}``` \n\nBy [@StringSessionGen_Bot](tg://openmessage?user_id=1472531255) \nA Bot By @KGSupportgroup")
        await client.disconnect()
        text = "String Session is Successfully Generated.\nClick on Below Button."
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Show String Session", url=f"tg://openmessage?user_id={chat.id}")]]
        )
        await bot.send_message(chat.id, text, reply_markup=reply_markup)
    except Exception as e:
        await bot.send_message(chat.id ,f"**ERROR:** `{str(e)}`")
        return


@bot.on_message(filters.private & filters.command("restart"))
async def restart(_, msg: Message):
    await msg.reply("Restarted Bot!")
    HU_APP.restart()


@bot.on_message(filters.private & filters.command("help"))
async def restart(_, msg: Message):
    out = f"""
Hi, {msg.from_user.mention}. Saya Adahal Bot Untuk Mengambil String Anda. \
Saya akan memberi Anda `STRING_SESSION` untuk UserBot Anda..

Perlu `API_ID`, `API_HASH`, Nomor Telepon dan Kode Verifikasi Satu Kali. \
Yang akan dikirim ke Nomor Telepon Anda.
Anda harus memasukkan **OTP** dalam `1 2 3 4 5` format ini. __(Spasi di antara setiap angka!)__

**CATATAN:** Jika bot tidak Mengirim OTP ke Nomor Telepon Anda, kirim /restart Command dan kirim lagi /start untuk Memulai Proses Anda.

Harus Bergabung dengan Saluran untuk Pembaruan Bot !!
"""
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton('Support Group', url='https://t.me/KGSupportgroup'),
                InlineKeyboardButton('Developer', url='https://t.me/knsgnwn')
            ],
            [
                InlineKeyboardButton('Bots Updates Channel', url='https://t.me/rakasupport'),
            ]
        ]
    )
    await msg.reply(out, reply_markup=reply_markup)


async def is_cancel(msg: Message, text: str):
    if text.startswith("/cancel"):
        await msg.reply("Process Cancelled.")
        return True
    return False

if __name__ == "__main__":
    bot.run()
