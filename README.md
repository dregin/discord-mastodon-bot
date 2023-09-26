# Introduction

This bot will watch your mastodon account for notifications of type `admin.report`.

It will parse the notification payload and post it to a Discord channel via webhook in this format:

```
Report received from dregotest against conor.
Note: Test report as the last one didn't send a notification for some reason...

Link: https://mastodon.ie/admin/reports/1254
```

# Configuration
Rename `.env.SAMPLE` to `.env` and update the variables with your own.

# Deployment
`docker-compose up -d`
