import os
import ssl
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from pytube import YouTube
from dotenv import load_dotenv

ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class DownloadStates(StatesGroup):
    waiting_for_url = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! YouTube video yuklovchi botga xush kelibsiz!\n\n"
                      "Video yuklash uchun linkni yuboring yoki /help buyrug'ini bosing.")

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = """
📌 Botdan foydalanish bo'yicha yo'riqnoma:

1. YouTube video linkini shu yerga yuboring
2. Bot video sifatini tanlash uchun variantlarni ko'rsatadi
3. Kerakli sifatni tanlang
4. Video yuklanadi va sizga jo'natiladi

⚠️ Eslatma: Ba'zi videolar muallif tomonidan yuklab olish uchun bloklangan bo'lishi mumkin.
    """
    await message.reply(help_text)

@dp.message_handler(state=DownloadStates.waiting_for_url)
async def process_url(message: types.Message, state: FSMContext):
    try:
        url = message.text
        yt = YouTube(url)
        
        title = yt.title
        duration = yt.length // 60  
        thumbnail_url = yt.thumbnail_url
        
        streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
        
        if not streams:
            await message.reply("⚠️ Kechirasiz, bu videoni yuklab bo'lmaydi.")
            await state.finish()
            return
        
        info_text = f"🎬 Video: {title}\n⏳ Davomiylik: {duration} daqiqa"
        await bot.send_photo(message.chat.id, thumbnail_url, caption=info_text)
        
        keyboard = types.InlineKeyboardMarkup()
        for stream in streams:
            button_text = f"{stream.resolution} ({stream.filesize_mb:.1f} MB)"
            callback_data = f"download_{stream.itag}"
            keyboard.add(types.InlineKeyboardButton(button_text, callback_data=callback_data))
        
        await message.reply("Quyidagi sifatlardan birini tanlang:", reply_markup=keyboard)
        await state.update_data(url=url)
        
    except Exception as e:
        await message.reply(f"⚠️ Xatolik yuz berdi: {str(e)}")
        await state.finish()

@dp.callback_query_handler(lambda c: c.data.startswith('download_'))
async def process_download(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    itag = callback_query.data.split('_')[1]
    
    user_data = await state.get_data()
    url = user_data.get('url')
    
    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)
        
        await bot.send_message(callback_query.from_user.id, "⏳ Video yuklanmoqda, iltimos kuting...")
        
        file_path = stream.download(output_path='downloads', filename_prefix='yt_')
        
        with open(file_path, 'rb') as video_file:
            await bot.send_video(
                chat_id=callback_query.from_user.id,
                video=video_file,
                caption=f"🎥 {yt.title}\n\n✅ Muvaffaqiyatli yuklandi!"
            )
        
        os.remove(file_path)
        
    except Exception as e:
        await bot.send_message(callback_query.from_user.id, f"⚠️ Xatolik yuz berdi: {str(e)}")
    
    await state.finish()

@dp.message_handler()
async def handle_message(message: types.Message, state: FSMContext):
    if 'youtube.com' in message.text or 'youtu.be' in message.text:
        await DownloadStates.waiting_for_url.set()
        await process_url(message, state)  
    else:
        await message.reply("Iltimos, YouTube video linkini yuboring yoki /help buyrug'ini bosing.")

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    executor.start_polling(dp, skip_updates=True)