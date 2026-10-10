import asyncio
import json
import tempfile
import unittest
from datetime import datetime
from itertools import count
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import nonebot
from nonebot.adapters.console import Adapter, Bot, Message
from nonebot.adapters.console.event import MessageEvent, MessageResponse
from nonechat.model import DIRECT, Channel, Robot, User


def setUpModule():
    global runtime, commands, storage, scheduled, bot
    runtime = tempfile.TemporaryDirectory()
    base = Path(runtime.name)
    nonebot.init(
        driver="~none+~httpx",
        command_start={"/", "!"},
        superusers={"999"},
        console_headless_mode=True,
        uninfo_cache=False,
        localstore_data_dir=base / "data",
        localstore_config_dir=base / "config",
        localstore_cache_dir=base / "cache",
    )
    nonebot.get_driver().register_adapter(Adapter)
    assert nonebot.load_plugin("nonebot_plugin_nowtime") is not None
    from nonebot_plugin_nowtime import commands, storage
    from nonebot_plugin_nowtime import scheduler as scheduled

    bot = Bot(nonebot.get_adapter(Adapter), Robot(id="10000"))


def tearDownModule():
    runtime.cleanup()


message_ids = count(1)


def event(text, *, private=False, role="admin", user_id=456):
    return MessageEvent(
        time=datetime.now(),
        self_id="10000",
        user=User(id=str(user_id), nickname=role),
        channel=DIRECT if private else Channel("789", "test"),
        message_id=str(next(message_ids)),
        message=Message(text),
    )


def subscription(group, adapter="Console", bot_id="10000", **kwargs):
    return storage.Subscription(str(group), adapter, bot_id, **kwargs)


class StorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "data" / "nowtime.json"
        self.legacy = Path(self.directory.name) / "old.json"
        self.store = storage.GroupStore(self.path, self.legacy)

    async def test_migration_and_new_file_precedence(self):
        self.legacy.write_text(
            json.dumps({"opened_groups": [123, "123", "00456"]}), encoding="utf-8"
        )
        original = self.legacy.read_bytes()
        await self.store.load()
        self.assertEqual(tuple(item.id for item in self.store.targets), ("123", "456"))
        self.assertEqual(self.legacy.read_bytes(), original)
        await self.store.set_enabled(subscription(123, "OneBot V11", ""), False)
        reloaded = storage.GroupStore(self.path, self.legacy)
        await reloaded.load()
        self.assertEqual(tuple(item.id for item in reloaded.targets), ("456",))
        self.assertTrue(all(item.adapter == "OneBot V11" for item in reloaded.targets))

    async def test_concurrent_updates_persist_without_loss(self):
        await self.store.load()
        await asyncio.gather(
            *(self.store.set_enabled(subscription(i), True) for i in range(1, 21))
        )
        self.assertEqual(
            {item.id for item in self.store.targets}, {str(i) for i in range(1, 21)}
        )
        self.assertFalse(await self.store.set_enabled(subscription(1), True))
        reloaded = storage.GroupStore(self.path)
        await reloaded.load()
        self.assertEqual(reloaded.targets, self.store.targets)

    async def test_write_failure_preserves_memory_and_disk(self):
        await self.store.load()
        before = self.path.read_bytes()
        with patch.object(Path, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                await self.store.set_enabled(subscription(123), True)
        self.assertEqual(self.store.targets, ())
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    async def test_platform_bot_and_channel_destinations_remain_distinct(self):
        await self.store.load()
        targets = (
            subscription("room-abc"),
            subscription("room-abc", adapter="Other"),
            subscription("room-abc", bot_id="20000"),
            subscription("room-abc", parent_id="guild-a", channel=True),
            subscription("room-abc", parent_id="guild-b", channel=True),
        )
        for target in targets:
            self.assertTrue(await self.store.set_enabled(target, True))
        reloaded = storage.GroupStore(self.path)
        await reloaded.load()
        self.assertEqual(reloaded.targets, targets)
        self.assertTrue(await reloaded.set_enabled(targets[0], False))
        self.assertEqual(reloaded.targets, targets[1:])
        self.assertEqual(reloaded.targets[-1].as_target().parent_id, "guild-b")

    async def test_corrupt_file_is_not_overwritten_or_replaced_by_legacy(self):
        self.path.parent.mkdir()
        self.path.write_text("invalid json", encoding="utf-8")
        self.legacy.write_text('{"opened_groups": [123]}', encoding="utf-8")
        with self.assertRaises(ValueError):
            await self.store.load()
        self.assertEqual(self.path.read_text(encoding="utf-8"), "invalid json")


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = storage.GroupStore(Path(self.directory.name) / "nowtime.json")
        await self.store.load()
        store_patch = patch.object(commands, "group_store", self.store)
        store_patch.start()
        self.addCleanup(store_patch.stop)
        api_patch = patch.object(
            Bot,
            "send",
            new_callable=AsyncMock,
            return_value=MessageResponse(message_id="1", channel_id="789"),
        )
        self.api = api_patch.start()
        self.addCleanup(api_patch.stop)
        from nonebot_plugin_uninfo import Member, Role
        from nonebot_plugin_uninfo.adapters import INFO_FETCHER_MAPPING

        # Console 不提供管理员角色，模拟平台返回的角色以验证通用权限。
        def member(data, user):
            roles = {"admin": "ADMINISTRATOR", "owner": "OWNER"}
            role = roles.get(user.name) if "channel_id" in data else None
            if "roles" in Member.__dataclass_fields__:
                return Member(user, roles=[Role(role)] if role else [])
            return Member(user, role=Role(role) if role else None)

        role_patch = patch.object(
            INFO_FETCHER_MAPPING["Console"], "extract_member", side_effect=member
        )
        role_patch.start()
        self.addCleanup(role_patch.stop)

    async def run_command(self, matcher, incoming):
        state = {}
        self.assertTrue(await matcher.check_perm(bot, incoming))
        self.assertTrue(await matcher.check_rule(bot, incoming, state))
        await matcher().run(bot, incoming, state)
        call = self.api.call_args
        return str(call.kwargs["message"] if "message" in call.kwargs else call.args[1])

    async def test_group_enable_list_disable(self):
        reply = await self.run_command(commands.enable_nowtime, event("/开启整点报时"))
        self.assertIn("已成功开启789", reply)
        reply = await self.run_command(commands.enable_nowtime, event("/开启整点报时"))
        self.assertIn("无需重复开启", reply)
        reply = await self.run_command(
            commands.list_matcher, event("/查看整点报时列表")
        )
        self.assertIn("789", reply)
        reply = await self.run_command(commands.disable_nowtime, event("/关闭整点报时"))
        self.assertIn("已成功关闭789", reply)
        self.assertEqual(self.store.targets, ())

    async def test_explicit_group_compact_and_configured_prefix(self):
        for text, target in [("/开启整点报时123", "123"), ("!开启整点报时 456", "456")]:
            reply = await self.run_command(
                commands.enable_nowtime, event(text, user_id=999)
            )
            self.assertIn(f"已成功开启{target}", reply)
        self.assertEqual(tuple(item.id for item in self.store.targets), ("123", "456"))

    async def test_admin_cannot_modify_another_group(self):
        reply = await self.run_command(
            commands.enable_nowtime, event("/开启整点报时 other-room")
        )
        self.assertIn("仅超级用户", reply)
        self.assertEqual(self.store.targets, ())
        reply = await self.run_command(
            commands.enable_nowtime, event("/开启整点报时 789", role="owner")
        )
        self.assertIn("已成功开启789", reply)

    async def test_private_superuser_and_permissions(self):
        reply = await self.run_command(
            commands.enable_nowtime, event("/开启整点报时", private=True, user_id=999)
        )
        self.assertIn("私聊开关需要输入指定群号", reply)
        reply = await self.run_command(
            commands.enable_nowtime,
            event("/开启整点报时 123", private=True, user_id=999),
        )
        self.assertIn("已成功开启123", reply)
        self.assertFalse(
            await commands.enable_nowtime.check_perm(
                bot, event("/开启整点报时", role="member")
            )
        )
        self.assertFalse(
            await commands.enable_nowtime.check_perm(
                bot, event("/开启整点报时 123", private=True)
            )
        )

    async def test_save_failure(self):
        with patch.object(self.store, "_write", side_effect=OSError("disk failure")):
            reply = await self.run_command(
                commands.enable_nowtime, event("/开启整点报时")
            )
        self.assertIn("保存配置失败", reply)
        self.assertEqual(self.store.targets, ())

    async def test_time_aliases_and_http_failure(self):
        response = httpx.Response(
            200,
            json={"msg": "时间", "nowtime": "12:00", "nxyj": "你好"},
            request=httpx.Request("GET", "https://example.com"),
        )
        with patch.object(
            httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=response
        ):
            for text in ("/现在时间", "/当前时间", "/北京时间"):
                reply = await self.run_command(commands.time_now, event(text))
                self.assertIn("12:00", reply)
        with patch.object(
            httpx.AsyncClient, "get", side_effect=httpx.ConnectError("offline")
        ):
            reply = await self.run_command(commands.time_now, event("/现在时间"))
        self.assertIn("查询时间失败", reply)

    async def test_scheduler_sends_text_when_voice_is_unsupported(self):
        await self.store.set_enabled(subscription(789), True)
        with (
            patch.object(scheduled, "group_store", self.store),
            patch.object(scheduled, "get_bots", return_value={bot.self_id: bot}),
            patch.object(scheduled.asyncio, "sleep", new_callable=AsyncMock),
            patch.object(
                Bot,
                "send_message",
                new_callable=AsyncMock,
                return_value=MessageResponse(message_id="1", channel_id="789"),
            ) as send,
        ):
            await scheduled.post_scheduler()
        send.assert_awaited_once()
        self.assertEqual(send.call_args.kwargs["channel_id"], "789")
        self.assertEqual(send.call_args.kwargs["message"][0].type, "text")

    async def test_scheduler_routes_each_subscription_to_its_own_bot(self):
        other = SimpleNamespace(
            self_id="20000", adapter=SimpleNamespace(get_name=lambda: "Other")
        )
        await self.store.set_enabled(subscription("shared"), True)
        await self.store.set_enabled(
            subscription(
                "shared",
                adapter="Other",
                bot_id="20000",
                parent_id="guild",
                channel=True,
            ),
            True,
        )
        await self.store.set_enabled(subscription("offline", bot_id="missing"), True)
        with (
            patch.object(scheduled, "group_store", self.store),
            patch.object(
                scheduled,
                "get_bots",
                return_value={bot.self_id: bot, other.self_id: other},
            ),
            patch.object(scheduled.asyncio, "sleep", new_callable=AsyncMock),
            patch.object(scheduled.UniMessage, "send", new_callable=AsyncMock) as send,
        ):
            await scheduled.post_scheduler()
        self.assertEqual(send.await_count, 4)
        self.assertEqual(
            [call.kwargs["bot"] for call in send.call_args_list],
            [bot, bot, other, other],
        )
        target = send.call_args.kwargs["target"]
        self.assertEqual(target.parent_id, "guild")
        self.assertTrue(target.channel)
