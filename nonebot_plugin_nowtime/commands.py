from httpx import AsyncClient, HTTPError
from nonebot.adapters import Bot, Event
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import (
    Alconna,
    AlconnaMatcher,
    Args,
    CommandMeta,
    Match,
    Target,
    UniMessage,
    on_alconna,
)
from nonebot_plugin_alconna.uniseg import get_target
from nonebot_plugin_uninfo import ADMIN

from .storage import Subscription, group_store

manage_permission = SUPERUSER | ADMIN()

time_now = on_alconna(
    Alconna("现在时间"),
    aliases={"当前时间", "北京时间"},
    use_cmd_start=True,
    block=True,
    priority=5,
)
enable_nowtime = on_alconna(
    Alconna("开启整点报时", Args["group_id?", str], meta=CommandMeta(compact=True)),
    use_cmd_start=True,
    block=True,
    priority=99,
    permission=manage_permission,
)
disable_nowtime = on_alconna(
    Alconna("关闭整点报时", Args["group_id?", str], meta=CommandMeta(compact=True)),
    use_cmd_start=True,
    block=True,
    priority=99,
    permission=manage_permission,
)
list_matcher = on_alconna(
    Alconna("查看整点报时列表"),
    use_cmd_start=True,
    block=True,
    priority=99,
    permission=manage_permission,
)


@time_now.handle()
async def show_time() -> None:
    await time_now.send(UniMessage.text("正在查看当前时间……"))
    try:
        async with AsyncClient() as client:
            response = await client.get(
                "https://v.api.aa1.cn/api/time-tx/index.php", timeout=30
            )
            response.raise_for_status()
            data = response.json()
        message = (
            f"⭐{data['msg']}⭐\n\n现在是北京时间:\n{data['nowtime']}"
            f"送你一句：\n⭐{data['nxyj']}⭐"
        )
    except (HTTPError, ValueError, KeyError, TypeError) as error:
        logger.warning(f"查询时间失败：{error!r}")
        await time_now.finish(UniMessage.text("查询时间失败，请稍后再试。"))
    await time_now.finish(UniMessage.text(message))


@list_matcher.handle()
async def list_groups(bot: Bot) -> None:
    groups = tuple(item.id for item in group_store.targets if item.matches_bot(bot))
    message = "当前打开整点报时的群聊有：\n" + ("\n".join(groups) if groups else "暂无")
    await list_matcher.finish(UniMessage.text(message))


async def change_status(
    bot: Bot,
    event: Event,
    matcher: AlconnaMatcher,
    group_id: Match[str],
    enabled: bool,
) -> None:
    current = get_target(event, bot)
    if group_id.available:
        if group_id.result != current.id and not await SUPERUSER(bot, event):
            await matcher.finish(
                UniMessage.text("仅超级用户可以管理其他群或频道的整点报时。")
            )
        target = Target(
            group_id.result,
            parent_id=current.parent_id if current.channel else "",
            channel=current.channel,
        )
    elif not current.private:
        target = current
    else:
        await matcher.finish(UniMessage.text("私聊开关需要输入指定群号"))
    subscription = Subscription.from_target(target, bot)
    try:
        changed = await group_store.set_enabled(subscription, enabled)
    except OSError as error:
        logger.error(f"保存整点报时配置失败：{error!r}")
        await matcher.finish(UniMessage.text("保存配置失败，请稍后再试。"))
    if not changed:
        message = "该群已经开启，无需重复开启" if enabled else "该群尚未开启，无需关闭"
    else:
        message = f"已成功{'开启' if enabled else '关闭'}{target.id}的整点报时"
    await matcher.finish(UniMessage.text(message))


@enable_nowtime.handle()
async def enable_group(
    bot: Bot, event: Event, matcher: AlconnaMatcher, group_id: Match[str]
) -> None:
    await change_status(bot, event, matcher, group_id, True)


@disable_nowtime.handle()
async def disable_group(
    bot: Bot, event: Event, matcher: AlconnaMatcher, group_id: Match[str]
) -> None:
    await change_status(bot, event, matcher, group_id, False)
