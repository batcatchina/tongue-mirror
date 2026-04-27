# 舌镜 MCP Server 使用文档

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [配置指南](#配置指南)
- [工具使用](#工具使用)
- [Claude Desktop集成](#claude-desktop集成)
- [测试验证](#测试验证)
- [常见问题](#常见问题)

---

## 概述

**舌镜 MCP Server** 是基于 Model Context Protocol (MCP) 的中医舌诊辨证辅助服务。它允许 AI Agent（如 Claude Desktop、Cursor 等）直接调用舌诊辨证功能，实现智能化的中医舌诊分析。

### 核心功能

| 功能 | 描述 |
|------|------|
| 🤖 舌诊辨证 | 基于舌象特征进行证型判断和针灸选穴推荐 |
| ✅ 特征验证 | 验证舌象特征的有效性和逻辑一致性 |
| 💉 穴位查询 | 根据证型或症状查询推荐穴位 |

### 技术规格

- **协议**：Model Context Protocol (MCP)
- **语言**：Python 3.8+
- **依赖**：mcp>=1.0.0, python-dotenv>=1.0.0
- **传输模式**：stdio（桌面集成）/ SSE（远程部署）

---

## 快速开始

### 1. 安装依赖

```bash
cd tongue-mcp-server
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件，填入您的 API Key
```

### 3. 运行服务器

**stdio 模式（用于 Claude Desktop）**：

```bash
python src/server.py
```

**SSE 模式（用于远程部署）**：

```bash
python src/server.py --transport sse --port 8080
```

---

## 配置指南

### 环境变量

| 变量名 | 必填 | 默认值 | 描述 |
|--------|------|--------|------|
| `TONGUE_API_KEY` | 是 | - | API 密钥 |
| `API_BASE_URL` | 否 | https://api.example.com/v1 | API 服务地址 |
| `SERVER_PORT` | 否 | 8080 | 服务器端口（SSE 模式） |
| `LOG_LEVEL` | 否 | INFO | 日志级别 |

### Claude Desktop 配置

1. 打开 Claude Desktop 配置目录：
   - **macOS**：`~/Library/Application Support/Claude/`
   - **Windows**：`%APPDATA%\Claude\`
   - **Linux**：`~/.config/Claude/`

2. 编辑或创建 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "tongue-mirror": {
      "command": "python",
      "args": ["/path/to/tongue-mcp-server/src/server.py"],
      "env": {
        "TONGUE_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

3. 重启 Claude Desktop

---

## 工具使用

### analyze_tongue

执行舌诊辨证分析。

**参数**：

```python
{
    "tongue_color": "红",           # 必填：舌色
    "tongue_shape": "瘦薄",        # 必填：舌形
    "tongue_coating_color": "黄",  # 必填：苔色
    "tongue_coating_texture": "薄", # 必填：苔质
    "patient_age": 45,             # 必填：患者年龄
    "patient_gender": "男",        # 必填：性别
    "chief_complaint": "胃脘胀满1周",  # 必填：主诉
    "symptoms": "口干咽燥",        # 可选：伴随症状
    "tongue_texture": "裂纹",      # 可选：舌面特征
    "tongue_movement": "正常",     # 可选：舌态
    "mode": "详细模式",           # 可选：辨证模式
    "language": "中文"            # 可选：输出语言
}
```

**返回值示例**：

```json
{
  "辨证结果": {
    "主要证型": "阴虚火旺证",
    "证型得分": 15,
    "置信度": 0.85,
    "病机": "肝肾阴虚，虚火上炎",
    "脏腑定位": ["肝", "肾"]
  },
  "针灸方案": {
    "治疗原则": "滋阴清热，养心安神",
    "主穴": [
      {"穴位": "太溪", "经络": "肾经", "功效": "滋阴降火"}
    ]
  },
  "生活调护建议": {
    "饮食建议": ["宜食银耳、百合、莲子等滋阴食物"],
    "生活起居": ["规律作息，避免熬夜"]
  }
}
```

### validate_tongue_features

验证舌象特征的有效性。

**参数**：

```python
{
    "features": "{\"tongue_color\":\"红\",\"tongue_shape\":\"胖大\"}"
}
```

**返回值示例**：

```json
{
  "is_valid": true,
  "warnings": ["红舌通常与瘦薄舌相关，与胖大舌组合较少见"],
  "errors": [],
  "suggestions": []
}
```

### query_acupoints

根据证型查询穴位。

**参数**：

```python
{
    "syndrome": "阴虚火旺证",  # 必填：中医证型
    "symptom": "失眠",         # 可选：具体症状
    "organ": "心",             # 可选：脏腑定位
    "limit": 5                 # 可选：返回数量
}
```

**返回值示例**：

```json
{
  "证型": "阴虚火旺证",
  "穴位总数": 5,
  "穴位列表": [
    {"穴位": "太溪", "经络": "肾经", "功效": "滋阴降火"},
    {"穴位": "照海", "经络": "肾经", "功效": "滋阴清热"}
  ]
}
```

---

## Claude Desktop 集成

### 集成步骤

1. **安装舌镜 MCP Server**：
   ```bash
   git clone <repository_url>
   cd tongue-mcp-server
   pip install -r requirements.txt
   ```

2. **配置 Claude Desktop**：
   
   编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：
   
   ```json
   {
     "mcpServers": {
       "tongue-mirror": {
         "command": "python",
         "args": ["/absolute/path/to/tongue-mcp-server/src/server.py"],
         "env": {
           "TONGUE_API_KEY": "your_api_key_here"
         }
       }
     }
   }
   ```

3. **重启 Claude Desktop**

4. **验证集成**：
   
   在 Claude Desktop 中输入：
   ```
   舌头发红，舌苔黄，有点裂纹，帮我分析一下
   ```

### 使用示例

```
用户：我的舌头比较红，舌苔黄而薄，有点裂纹，这是什么情况？

Agent：[调用 analyze_tongue 工具]

根据您的舌象分析：

【辨证结果】
- 主要证型：阴虚火旺证（置信度：85%）
- 病机：肝肾阴虚，虚火上炎
- 涉及脏腑：肝、肾

【舌象特征解读】
- 舌红主热，提示阴虚火旺
- 苔黄主热，与舌红相应
- 裂纹提示阴液不足

【针灸方案】
- 治疗原则：滋阴清热，养心安神
- 主穴：太溪（肾经）、照海（肾经）、三阴交（脾经）
- 配穴：神门（心经）、合谷（大肠经）

【生活调护】
- 饮食：宜食银耳、百合、莲子等滋阴食物
- 忌食辛辣刺激食物
- 起居：规律作息，避免熬夜
- 运动：以柔和运动为主，如太极拳

⚠️ 免责声明：本分析仅供参考，不能替代专业医师诊断。
```

---

## 测试验证

### 本地测试

```bash
cd tongue-mcp-server
python -m pytest tests/ -v
```

### 手动测试

1. 启动服务器：
   ```bash
   python src/server.py
   ```

2. 使用 MCP Inspector 测试：
   ```bash
   npx @anthropic-ai/mcp-inspector
   ```

### Claude Desktop 测试

1. 重启 Claude Desktop
2. 检查 MCP 服务器状态
3. 发送测试请求

### OpenClaw 测试

```bash
openclaw skill install ./skills/tongue-diagnosis
openclaw skill test tongue-diagnosis-assistant
```

---

## 常见问题

### Q: Claude Desktop 无法连接 MCP Server？

**A**: 检查以下内容：
1. 配置文件路径是否正确
2. Python 路径是否正确
3. API Key 是否设置
4. 重启 Claude Desktop

### Q: 返回 "未知工具" 错误？

**A**: 确保工具名称正确：
- `analyze_tongue`
- `validate_tongue_features`
- `query_acupoints`

### Q: 如何处理敏感信息？

**A**: 
- API Key 存储在环境变量中，不要硬编码
- 用户隐私数据不持久化存储
- 使用 HTTPS 传输

---

## 更新日志

### v1.0.0 (2026-04-22)
- 初始版本发布
- 支持舌诊辨证、特征验证、穴位查询三大功能
- 兼容 Claude Desktop 和 OpenClaw 生态
