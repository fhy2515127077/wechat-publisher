# 公众号自动发布 — 配置指南

## 1. 获取凭证

1. 登录 [微信公众平台](https://mp.weixin.qq.com/)
2. 左侧菜单：**设置与开发** → **基本配置**
3. 找到 `AppID` 和 `AppSecret`
4. 填入 `scripts/config.json`

## 2. IP 白名单（必做！）

微信公众号 API 要求调用方 IP 在白名单中，否则返回：
```
errcode: 40164
errmsg: invalid ip xxx.xxx.xxx.xxx, not in whitelist
```

**操作步骤：**
1. 公众号后台 → 设置与开发 → 基本配置
2. 找到 **IP白名单** → 点击修改
3. 添加你的公网 IP（可访问 https://ip.sb 查询）
4. 保存

⚠️ **注意**：IP 白名单变更后立即生效，但如果 IP 变了（比如换了网络/VPN），需要重新添加。

## 3. 公众号类型要求

| 类型 | 发布权限 | 说明 |
|------|---------|------|
| 服务号（已认证） | ✅ 完整 API | 可直接调用发布接口 |
| 订阅号（已认证） | ⚠️ 部分 | 需确认已开通「发布」接口 |
| 订阅号（未认证） | ❌ 无 | 无法使用草稿/发布 API |

如果不确定，可在公众号后台 → 设置与开发 → 基本配置 → 接口权限 中查看。

## 4. 验证凭证

```bash
curl -s 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=YOUR_APPID&secret=YOUR_SECRET'
```

成功返回：
```json
{"access_token": "xxx", "expires_in": 7200}
```

失败返回：
```json
{"errcode": 40164, "errmsg": "invalid ip ... not in whitelist"}
```

## 5. 封面图

发布文章必须有封面图。准备一张 **900×383px** 或 **2.35:1** 比例的图片，通过 `--cover` 参数指定路径。

## 6. access_token 缓存

脚本会自动缓存 access_token（有效期 2 小时），缓存在 `scripts/token_cache.json`。无需手动管理。
