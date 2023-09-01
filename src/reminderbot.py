import asyncio
import logging
import sys
import config

from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

logging.basicConfig(filename="log.txt",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

TOKEN = config.BOT_TOKEN

form_router = Router()

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


class Form(StatesGroup):
    name = State()
    like_bots = State()


chatId = 0
flag = True
timeSend = config.TIME_SEND


@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    global chatId
    chatId = message.chat.id
    await state.set_state(Form.like_bots)
    await message.answer(
        config.MESSAGE_START,
        reply_markup=ReplyKeyboardRemove(),
    )

    await timer_send_message(timeSend, message)


@form_router.message(Command("cancel"))
@form_router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        config.MESSAGE_CANCEL,
        reply_markup=ReplyKeyboardRemove(),
    )


@form_router.message(Form.like_bots, F.text.casefold() == "no")
async def process_dont_like_write_bots(message: Message) -> None:
    time_delta = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")
    await reply_sticker(config.STICKER_BAD)
    await reply_message(config.MESSAGE_NO, message)
    global flag
    flag = True
    await timer_send_message(time_delta, message)


@form_router.message(Form.like_bots, F.text.casefold() == "yes")
async def process_like_write_bots(message: Message) -> None:
    global flag
    flag = True
    await reply_sticker(config.STICKER_GOOD)
    await reply_message(config.MESSAGE_YES, message)
    await timer_send_message(timeSend, message)


@form_router.message()
async def process_unknown_write_bots(message: Message) -> None:
    logging.info({message.text, message.chat.id, message.date})
    await message.reply(config.MESSAGE_UNKNOWN)


async def timer_send_message(time_str: str, message: Message) -> None:
    logging.info({message.text, message.chat.id, message.date})
    global flag
    while flag:
        if datetime.now().strftime("%H:%M") == time_str:
            await reply_sticker(config.STICKER_JOB)
            await bot.send_message(chatId, text=config.MESSAGE_SEND, reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Yes"),
                        KeyboardButton(text="No"),
                    ]
                ],
                resize_keyboard=True,
            ))

            flag = False


async def reply_message(text: str, message: Message) -> None:
    logging.info({message.text, message.chat.id, message.date})
    await bot.send_message(chatId, text=text, reply_markup=ReplyKeyboardRemove())


async def reply_sticker(patch: str) -> None:
    await bot.send_sticker(chatId, patch)


async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
