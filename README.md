# U2B2B

自动化搬运 [YouTube](https://www.youtube.com/) 视频至 [Bilibili](https://www.bilibili.com/)

**注意：为避免侵权，搬运前请先征得原 YouTuber 同意**

## Feature

- 支持多B站用户对多 YouTube 频道
- 只搬运有自动字幕的视频，且实现了字幕硬压
- 搬运结束后自动点赞指定分区视频，以获取关注

## Usage

1. [下载 ffmpeg](https://www.ffmpeg.org/download.html)，并确保其路径位于环境变量中
2. `pip install -r requirements.txt`
3. 复制 `setting_sample.json` 为 `setting.json` ，根据实际情况修改 COOKIE 等内容
4. `python u2b2b.py`；或将其添加为计划任务定时运行

## `sample.json`内容说明

```json
{
    "proxy": 代理地址(直连留空),
    "users": [
        {
            "cookie": COOKIE,
            "tid": 投稿分区 ID,
            "like": { "count": 点赞评论数, "sleep": 点赞间隔(秒) },
            "tags": [视频标签(会与原视频标签合并)],
            "channels": [油管频道 ID],
            "last_updated": ""
        }
    ]
}
```

## Changelog

- v1.0: 实现自动搬运、自动字幕硬压等基本功能

## Demo
- [U2B2B数码](https://space.bilibili.com/2086473161/video)
