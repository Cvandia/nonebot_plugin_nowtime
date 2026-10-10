import asyncio
import json
from datetime import datetime
from pathlib import Path

from nonebot import get_bots
from nonebot.exception import AdapterException
from nonebot.log import logger
from nonebot_plugin_alconna import SerializeFailed, UniMessage
from nonebot_plugin_apscheduler import scheduler

from . import plugin_config
from .storage import group_store

with (Path(__file__).parent / "resource/time_words.json").open(
    encoding="utf-8"
) as file:
    words_for_time: dict[str, str] = json.load(file)


def get_word_result(hour: int) -> str:
    return words_for_time.get(str(hour), "整点报时出错了！")


async def post_scheduler() -> None:
    hour = datetime.now().hour
    if hour not in range(plugin_config.start_time, plugin_config.end_time):
        return
    bots = tuple(get_bots().values())
    for subscription in group_store.targets:
        bot = next((bot for bot in bots if subscription.matches_bot(bot)), None)
        if bot is None:
            continue
        target = subscription.as_target()
        messages = (
            UniMessage.voice(
                url=f"https://v.api.aa1.cn/api/api-baoshi/data/baoshi/{hour}.mp3"
            ),
            UniMessage.text(get_word_result(hour)),
        )
        for message in messages:
            try:
                await message.send(target=target, bot=bot, fallback=False)
            except (
                AdapterException,
                SerializeFailed,
                NotImplementedError,
            ) as error:
                logger.warning(f"定时发送整点报时到 {subscription.id} 失败：{error!r}")
            await asyncio.sleep(1)


scheduler.add_job(
    post_scheduler, "cron", hour="*", id="everyday_nowtime", replace_existing=True
)
