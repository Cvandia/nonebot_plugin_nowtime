"""群开关持久化；旧路径仅用于首次迁移。"""

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from nonebot import logger
from nonebot.adapters import Bot
from nonebot_plugin_alconna import Target
from nonebot_plugin_localstore import get_plugin_data_file


@dataclass(frozen=True)
class Subscription:
    id: str
    adapter: str
    bot_id: str
    parent_id: str = ""
    channel: bool = False

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, str)
            for value in (self.id, self.adapter, self.bot_id, self.parent_id)
        ):
            raise ValueError("订阅标识必须为字符串")
        if (
            not self.id.strip()
            or not self.adapter
            or not isinstance(self.channel, bool)
        ):
            raise ValueError("订阅数据格式错误")

    @classmethod
    def from_target(cls, target: Target, bot: Bot) -> "Subscription":
        return cls(
            target.id,
            bot.adapter.get_name(),
            bot.self_id,
            target.parent_id,
            target.channel,
        )

    def matches_bot(self, bot: Bot) -> bool:
        return self.adapter == bot.adapter.get_name() and (
            not self.bot_id or self.bot_id == bot.self_id
        )

    def as_target(self) -> Target:
        return Target(self.id, parent_id=self.parent_id, channel=self.channel)

    def same_destination(self, other: "Subscription") -> bool:
        return (
            self.id == other.id
            and self.adapter == other.adapter
            and self.parent_id == other.parent_id
            and self.channel == other.channel
            and (not self.bot_id or not other.bot_id or self.bot_id == other.bot_id)
        )


class GroupStore:
    def __init__(self, path: Path, legacy_path: Optional[Path] = None) -> None:
        self.path = path
        self.legacy_path = legacy_path
        self._targets: tuple[Subscription, ...] = ()
        self._lock = asyncio.Lock()

    @property
    def targets(self) -> tuple[Subscription, ...]:
        return self._targets

    @staticmethod
    def _read(path: Path) -> tuple[Subscription, ...]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "targets" in data:
            if not isinstance(data["targets"], list):
                raise ValueError(f"订阅数据格式错误：{path}")
            targets = []
            for item in data["targets"]:
                if not isinstance(item, dict):
                    raise ValueError(f"订阅数据格式错误：{path}")
                try:
                    target = Subscription(**item)
                except TypeError as error:
                    raise ValueError(f"订阅数据格式错误：{path}") from error
                if target not in targets:
                    targets.append(target)
            return tuple(targets)
        if not isinstance(data, dict) or not isinstance(
            data.get("opened_groups"), list
        ):
            raise ValueError(f"群开关数据格式错误：{path}")
        groups = []
        for group in data["opened_groups"]:
            if isinstance(group, bool) or not isinstance(group, (str, int)):
                raise ValueError(f"群号格式错误：{group!r}")
            if not str(group).isascii() or not str(group).isdigit() or int(group) <= 0:
                raise ValueError(f"群号格式错误：{group!r}")
            group_id = str(int(group))
            if group_id not in groups:
                groups.append(group_id)
        # 旧配置来自此适配器，限定路由避免发到其他平台的同名群。
        return tuple(Subscription(group, "OneBot V11", "") for group in groups)

    def _write(self, targets: tuple[Subscription, ...]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.path.parent, delete=False
            ) as file:
                temporary = Path(file.name)
                json.dump(
                    {"targets": [asdict(target) for target in targets]},
                    file,
                    ensure_ascii=False,
                    indent=4,
                )
                file.write("\n")
            temporary.replace(self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    async def load(self) -> None:
        async with self._lock:
            try:
                groups = await asyncio.to_thread(self._read, self.path)
            except FileNotFoundError:
                groups = ()
                if self.legacy_path is not None:
                    try:
                        groups = await asyncio.to_thread(self._read, self.legacy_path)
                    except FileNotFoundError:
                        pass
                    else:
                        logger.info(
                            "旧整点报时配置已读取，将迁移至 localstore，原文件保留"
                        )
                await asyncio.to_thread(self._write, groups)
            self._targets = groups

    async def set_enabled(self, target: Subscription, enabled: bool) -> bool:
        async with self._lock:
            exists = any(item.same_destination(target) for item in self._targets)
            if exists == enabled:
                return False
            groups = (
                (*self._targets, target)
                if enabled
                else tuple(
                    item for item in self._targets if not item.same_destination(target)
                )
            )
            await asyncio.to_thread(self._write, groups)
            self._targets = groups
            return True


group_store = GroupStore(
    get_plugin_data_file("nowtime.json"),
    legacy_path=Path("config/nowtime.json"),
)
