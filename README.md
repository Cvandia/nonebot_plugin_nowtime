
<div align="center">

<a href="https://v2.nonebot.dev/store"><img src="https://img.zcool.cn/community/014c9a55420cdc0000019ae952d851.jpg@1280w_1l_2o_100sh.jpg" width="180" height="180" alt="NoneBotPluginLogo"></a>

</div>

<div align="center">

# nonebot-plugin-nowtime

_⭐基于Nonebot2的一款整点报时的插件⭐_


</div>

<div align="center">
<a href="https://www.python.org/downloads/release/python-390/"><img src="https://img.shields.io/badge/python-3.8+-blue"></a>  <a href=""><img src="https://img.shields.io/badge/QQ-1141538825-yellow"></a> <a href="https://github.com/Cvandia/nonebot_plugin_nowtime/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue"></a> <a href="https://v2.nonebot.dev/"><img src="https://img.shields.io/badge/Nonebot2-rc1+-red"></a>
</div>


## ⭐ 介绍

__基于`nonebot-plugin-apscheduler`__
让bot为你整点报时吧

## 💿 安装

<details>
<summary>nb-cli安装</summary>

在项目目录文件下运行

```
nb plugin install nonebot_plugin_nowtime
```

</details>

<details>
<summary>pip安装</summary>

```
pip install nonebot-plugin-nowtime
```

</details>

## 🛠️ 开发

使用 [uv](https://docs.astral.sh/uv/) 管理依赖和构建项目：

```bash
uv sync --locked
uv run pre-commit install
uv run pre-commit run --all-files
```

提交前会自动检查文件格式，并使用 Ruff 检查和格式化 Python 代码。
也可以手动检查或构建发布包：

```bash
uv run ruff check .
uv run ruff format --check .
uv run python -m unittest discover -s tests -v
uv build
```

## 🚀 自动测试与发布

推送到 `main` 或向 `main` 提交 PR 时，GitHub Actions 会在 Python 3.9–3.13 上
安装锁定依赖，执行 Ruff 检查、单元测试并构建发布包。

发布沿用 game-torrent 的 PyPI Token 方式：

1. 在 GitHub 仓库的 `Settings → Secrets and variables → Actions` 中添加
   `PYPI_API_TOKEN`，值为该 PyPI 项目的 API Token。
2. 更新 `pyproject.toml` 的版本号及 `uv.lock`，提交改动。
3. 推送与版本号一致的 `v` 标签，例如版本 `0.2.0` 对应 `v0.2.0`。

标签触发后会先运行完整测试矩阵，全部通过且标签与版本一致时才上传到 PyPI。

## ⚙️ 配置

在全局配置文件`.env`中添加如下
```
start_time = 8
end_time = 20
```
>默认下配置为24小时全天播报，所以觉得很烦的请自行设置时间（采用24小时制）

群开关数据由 `nonebot-plugin-localstore` 管理，保存至插件数据目录的
`nowtime.json`。首次启动时，如果新文件不存在，会自动读取运行目录下旧的
`config/nowtime.json` 并迁移，原文件保留；后续以新文件为准。
可通过 `nb localstore` 查看存储目录，或通过 localstore 配置自定义数据路径。

插件不依赖固定适配器，消息通过 Alconna 发送，管理员与群主权限由
`nonebot-plugin-uninfo` 获取。可用平台为两者共同支持的适配器；平台未提供角色信息时，
由超级用户管理报时。语音支持取决于平台，不支持语音时仍会发送文字报时。

每条订阅记录适配器、机器人、群或频道 ID，并保留频道的父级 ID。
旧版群号列表按原平台保留，不会转发到其他平台；切换平台后请重新开启报时。

## ⭐ 使用

### 指令：
| 指令 | 需要@ | 范围 | 说明 |权限|
|:-----:|:----:|:----:|:----:|:----:|
|北京时间|否|私聊、群聊|查看现在时间|任何|
|开启、关闭整点报时 [群号]|否|群聊、私聊|省略群号操作当前群；私聊必须指定群号|群主，超管，管理员（私聊仅超管）|
|查看整点报时列表|否|群聊|查看已开启整点报时的群聊|群主，超管，管理员|

如：
```
/开启整点报时
```

**注意**

默认情况下, 您应该在指令前加上命令前缀, 通常是 `/`

命令由 `nonebot-plugin-alconna` 解析，遵循 NoneBot 的 `COMMAND_START` 配置。
指定群号时可使用 `/开启整点报时 123456`，也兼容 `/开启整点报时123456`。
群或频道 ID 支持字符串，省略 ID 时操作当前群或频道；列表只显示当前机器人的订阅。
群主和管理员只能管理当前群或频道，跨群操作仅限超级用户。

## 🌙 未来todo

- [x] 添加语音整点报时
- [x] 自定义播报时间
- [ ] 优化整点报时词库
- [ ] 图片整点报时

## ❤️ 鸣谢
- [nonebot-plugin-apscheduler](https://github.com/nonebot/plugin-apscheduler)
-  Python 聊天机器人框架[Nonebot2](https://github.com/nonebot/nonebot2)
