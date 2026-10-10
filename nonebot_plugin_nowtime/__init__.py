from nonebot import get_driver, get_plugin_config, require
from nonebot.plugin import PluginMetadata

from .config import Config

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_apscheduler")

__plugin_meta__ = PluginMetadata(
    name="整点报时",
    description="每时每刻正点报时",
    usage="现在时间 / 当前时间 / 北京时间\n查看整点报时列表\n开启整点报时 [群号]\n关闭整点报时 [群号]",
    config=Config,
    type="application",
    homepage="https://github.com/Cvandia/nonebot_plugin_nowtime",
    supported_adapters=(
        require("nonebot_plugin_alconna").__plugin_meta__.supported_adapters
        & require("nonebot_plugin_uninfo").__plugin_meta__.supported_adapters
    ),
    extra={
        "unique_name": "nonebot-plugin-nowtime",
        "author": "divandia <106718176+Cvandia@users.noreply.github.com>",
        "version": "0.3.0",
    },
)

plugin_config = get_plugin_config(Config)

from . import commands, scheduler  # noqa: E402, F401
from .storage import group_store  # noqa: E402

get_driver().on_startup(group_store.load)
