import pandas as pd
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes
import logging
import os
import random
from telegram.helpers import mention_markdown

#Token API MicinBot
TOKEN = 'MY_TOKEN'

#Konfigurasi logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# File data CSV
CSV_FILE = "user_data.csv"

# Membaca data pengguna dari CSV
def read_user_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE, index_col=0)
    else:
        return pd.DataFrame(columns=['user_id', 'username', 'grup_id'])

# Menyimpan data pengguna ke CSV
def save_user_data(df):
    df.to_csv(CSV_FILE)

# Membagi list user ke dalam chunks
def chunks(elements, size):
    n = max(1, size)
    return (elements[i:i+n] for i in range(0, len(elements)))

# Mengatasi unicode
def unicode_truncate(s, length, encoding='utf-8'):
    encoded = s.encode(encoding)[:length]
    return encoded.decode(encoding, 'ignore')

# Handler untuk '/daftar'
async def register(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or "Anonymous"
    grup_id = update.message.chat.id
    chat_id = update.effective_chat.id

    df = read_user_data()
    pesan = mention_markdown(user_id=user_id, name=unicode_truncate(username, 100), version=2)
    if not ((df['user_id'] == user_id) & (df['grup_id'] == grup_id)).any():
        df2 = pd.DataFrame({'user_id': user_id, 'username': username, 'grup_id': grup_id}, index=[0])
        df = pd.concat([df, df2], ignore_index=True)
        save_user_data(df)
        await update.message.reply_text(f"Hai, {pesan}, kamu sekarang tercatat dan akan aku mention nanti\. Terima kasih\!", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text(f"{pesan}, kamu sudah tercatat sebelumnya\. Terima kasih\!", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)

# Handler untuk '/keluar'
async def unregister(update: Update, context:CallbackContext):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    grup_id = update.message.chat.id

    df = read_user_data()
    try:
        df = df.drop(df[(df['user_id'] == user_id) & (df['grup_id'] == grup_id)].index)
    except:
        pass
    save_user_data(df)
    await update.message.reply_text("Kamu sudah tidak tercatat.")

# Handler untuk '/mention'
async def mention_members(update:Update, context:CallbackContext):
    grup_id = update.message.chat.id
    chat_id = update.effective_chat.id
    df = read_user_data()
    df_grup = df[df['grup_id'] == grup_id]
    grup_dict = dict(zip(df_grup['user_id'], df_grup['username']))
    user_id_list = random.sample(df_grup['user_id'].tolist(), len(df_grup))
    name_list = [grup_dict[ids] for ids in user_id_list]
    mention_dict = dict(zip(user_id_list, name_list))
    print(mention_dict)

    # Menyebutkan pengguna
    if user_id_list:
        mentions = [mention_markdown(user_id, unicode_truncate(user_name, 100), version=2) for user_id, user_name in mention_dict.items()]
        if len(user_id_list) <= 5:
            message = " ".join(mentions)
            await context.bot.send_message(chat_id=chat_id, text = message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
        elif len(user_id_list) > 5:
            for i in range(0, len(user_id_list), 5):
                selected = mentions[i:i+5]
                message = " ".join(selected)
                await context.bot.send_message(chat_id=chat_id, text = message, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Tidak ada pengguna terdaftar.")

# Handler untuk '/mulai'
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Halo! Saya adalah bot pemanggil.\nUntuk dapat ikut dipanggil ketika ada perintah /mention, kamu perlu memperkenalkan diri dengan perintah /daftar. Apabila kamu tidak ingin dipanggil ketika ada perintah /mention, gunakan perintah /keluar.\nUntuk penjelasan dan perubahan, hubungi @breezecalaf.\nTerima kasih!")

# Fungsi Utama
def main():
    aplikasi = Application.builder().token(TOKEN).build()
    aplikasi.add_handler(CommandHandler("mulai", start))
    aplikasi.add_handler(CommandHandler("daftar", register))
    aplikasi.add_handler(CommandHandler("keluar", unregister))
    aplikasi.add_handler(CommandHandler("mention", mention_members))

    aplikasi.run_polling()

if __name__ == "__main__":
    main()