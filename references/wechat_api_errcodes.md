# 微信公众号 API 常见错误码

## 认证相关

| errcode | 含义 | 解决 |
|---------|------|------|
| 40001 | access_token 无效或已过期 | 重新获取 token |
| 40002 | 不合法的凭证类型 | 检查 grant_type 参数 |
| 40013 | 不合法的 AppID | 检查 appid 是否正确 |
| 40014 | 不合法的 access_token | 重新获取 token |
| 40164 | **IP 不在白名单中**（最常见） | 去公众号后台添加当前公网 IP 到白名单 |
| 40166 | IP 白名单功能未开启 | 公众号后台 → 设置与开发 → 基本配置 → 开启 IP 白名单 |

## 素材相关

| errcode | 含义 | 解决 |
|---------|------|------|
| 40007 | 不合法的媒体文件 ID | media_id 不存在或已过期 |
| 40009 | 不合法的图片文件大小 | 图片不超过 10MB（永久）/ 64KB（临时） |
| 40010 | 不合法的图片类型 | 支持 BMP/PNG/JPEG/GIF |
| 45009 | API 调用次数超限 | 等待配额恢复或申请提高限额 |

## 发布相关

| errcode | 含义 | 解决 |
|---------|------|------|
| 45028 | 超过每月发布次数限制 | 订阅号每月限制，服务号更宽松 |
| 45064 | 创建草稿失败 | 检查 article 字段是否完整 |
| 48001 | 功能未授权 | 确认公众号类型支持该接口 |

## 常用 API 接口一览

```
获取 token:      GET  /cgi-bin/token
上传永久素材:     POST /cgi-bin/material/add_material
上传正文图片:     POST /cgi-bin/media/uploadimg
创建草稿:        POST /cgi-bin/draft/add
发布:            POST /cgi-bin/freepublish/submit
查询发布状态:     POST /cgi-bin/freepublish/get
```

## 测试凭证连通性（推荐用 curl）

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=YOUR_APPID&secret=YOUR_SECRET"
```

返回 `"access_token":"..."` 表示成功。
返回 `errcode` 表示需要排查上述问题。
