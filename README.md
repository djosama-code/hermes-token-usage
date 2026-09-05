# hermes-token-usage

Hermes 桌面的 Token 用量监控 —— **底部实时用量条** + **`/usage` 历史详情页**，思路对标
DeepSeek Harness 的 dsh-token-usage 插件。数据全部来自 Hermes **自带的** `state.db`
（`session_model_usage` 表），**不拦截请求、不改库、不偷听内容**。

- 底部条：实时显示**当前会话**的 输入 / 输出 / 缓存命中率 / 总 token / 调用次数 / 费用
  （走 `host.state.focusedUsage`，0.21.0 起原生带缓存命中率与费用，无需后端）。
- 详情页 `/usage`：点底部条打开 —— 全局总量、估算费用、按 provider/model、按会话 Top30、
  近 30 天逐日趋势（走后端 `plugin_api.py` 直读 `state.db` 聚合）。

**注意**：仅实测于 Hermes 0.21.0 桌面端（Electron）。其余版本需自行验证。

---

## 安装（换一台电脑即可用）

### 方式 A —— 单文件安装器（推荐）
```bash
python install_hermes_usage.py            # 完整版：底部条 + 详情页（自动探测 HERMES_HOME、写文件、加入启用白名单、备份 config）
python install_hermes_usage.py --bar-only # 极简版：只装底部实时条，免改配置、零后端依赖
```
装完：**彻底退出 Hermes 桌面端（含托盘）再打开**；底部条没出现就 `Ctrl+K` → `Reload desktop plugins`。

### 方式 B —— 手动放置
把 `plugin/` 里的两个子目录原样并入你的 Hermes 数据目录（`$HERMES_HOME`，Windows 常见为
`%LOCALAPPDATA%\hermes` 或 `~/.hermes`）：

```
plugin/desktop-plugins/hermes-usage/plugin.js                       → <home>/desktop-plugins/hermes-usage/plugin.js
plugin/plugins/hermes-usage/dashboard/manifest.json                 → <home>/plugins/hermes-usage/dashboard/manifest.json
plugin/plugins/hermes-usage/dashboard/plugin_api.py                 → <home>/plugins/hermes-usage/dashboard/plugin_api.py
```
然后确保 `<home>/config.yaml` 的 `plugins.enabled` 含 `hermes-usage`（仅详情页需要；
底部条不依赖它），再重启桌面端。

---

## 关于启用开关（只影响详情页后端）
- `desktop-plugins/hermes-usage/plugin.js`：桌面插件，落地即自动加载（默认启用）。
- `plugins/hermes-usage/dashboard/plugin_api.py`：详情页的 Python 后端，须在
  `plugins.enabled` 白名单里、并在 **gateway 重启后**才会挂载到
  `/api/plugins/hermes-usage/`（安全边界，非默认）。底部条不依赖它。

---

## 目录
```
install_hermes_usage.py               # 单文件自包含安装器（内嵌全部插件源码）
plugin/
├── desktop-plugins/hermes-usage/plugin.js          # 桌面端：底部条 + /usage 页 + ⌘K
└── plugins/hermes-usage/dashboard/
    ├── manifest.json                                # 声明后端 api 入口
    └── plugin_api.py                                # 读 state.db 的聚合后端
```

## 数据口径说明
- 底部条命中率/费用来自 Hermes 后端实时 `UsageStats`，是**精确值**。
- 详情页 "缓存 ÷ 输入" 是**读取放大倍数**（Hermes 累计口径），**不是命中率**，已标注避免误解。
- 费用为本地估算，不冒充 provider 账单。

## License
MIT © djosama-code
