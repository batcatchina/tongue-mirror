# 舌镜 MCP Server

基于Model Context Protocol (MCP) 的中医舌诊辨证辅助服务。

## 功能特性

- 🤖 **MCP协议兼容**：支持Claude Desktop、Cursor等MCP客户端
- 🔍 **舌诊辨证**：基于舌象特征的智能辨证分析
- ✅ **特征验证**：舌象特征的有效性检验
- 💉 **穴位查询**：根据证型推荐针灸穴位

## 快速开始

### 安装依赖

```bash
pip install mcp python-dotenv
```

### 配置环境

创建 `.env` 文件：

```env
TONGUE_API_KEY=your_api_key_here
API_BASE_URL=https://api.example.com/v1
```

### 运行服务器

```bash
# stdio模式（用于Claude Desktop）
python src/server.py

# SSE模式（用于远程部署）
python src/server.py --transport sse --port 8080
```

## Claude Desktop配置

在 `~/Library/Application Support/Claude/claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "tongue-mirror": {
      "command": "python",
      "args": ["/path/to/tongue-mcp-server/src/server.py"],
      "env": {
        "TONGUE_API_KEY": "your_api_key"
      }
    }
  }
}
```

## 可用工具

### analyze_tongue
执行舌诊辨证分析

### validate_tongue_features
验证舌象特征有效性

### query_acupoints
根据证型查询穴位

## License

Apache 2.0
