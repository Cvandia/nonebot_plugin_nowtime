
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

## ⚙️ 配置

在全局配置文件`.env`中添加如下
```
start_time = 8
end_time = 20
```
>默认下配置为24小时全天播报，所以觉得很烦的请自行设置时间（采用24小时制）

## ⭐ 使用

### 指令：
| 指令 | 需要@ | 范围 | 说明 |权限|
|:-----:|:----:|:----:|:----:|:----:|
|北京时间|否|私聊、群聊|查看现在时间|任何|
|开启、关闭整点报时|否|群聊|开启或关闭群聊的整点报时|群主，超管，管理员|
|查看整点报时列表|否|群聊|查看已开启整点报时的群聊|群主，超管，管理员|

如：
```
/开启整点报时
```    

**注意**

默认情况下, 您应该在指令前加上命令前缀, 通常是 `/`

## 🌙 未来todo

- [x] 添加语音整点报时
- [x] 自定义播报时间  
- [ ] 优化整点报时词库
- [ ] 图片整点报时

## ❤️ 鸣谢
- [nonebot-plugin-apscheduler](https://github.com/nonebot/plugin-apscheduler)
-  Python 聊天机器人框架[Nonebot2](https://github.com/nonebot/nonebot2)