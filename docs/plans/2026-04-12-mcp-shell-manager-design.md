# MCP Shell Manager Design

**目标**

为本机常用 MCP 服务提供统一的 shell 命令面：

```bash
mcp <service> <action>
```

第一批服务为：

- `gsc`
- `ads`

第一批动作为：

- `start`
- `stop`
- `restart`
- `status`
- `logs`

## 1. 设计约束

- 不把复杂逻辑直接写进 `~/.zshrc`
- 真正逻辑放在独立 shell 文件，由 `~/.zshrc` 负责 `source`
- 使用 `tmux` 作为后台常驻载体
- 第一版只支持本机固定服务映射，不做动态注册
- 第一版不做 `all start`、不开机自启、不做复杂端口探测

## 2. 文件布局

建议在本机配置目录使用：

- `~/.config/mcp-manager/CLAUDE.md`
- `~/.config/mcp-manager/mcp.sh`

其中：

- `mcp.sh` 暴露 `mcp` shell function
- `~/.zshrc` 只保留一行：

```bash
source ~/.config/mcp-manager/mcp.sh
```

## 3. 命令面

统一入口：

```bash
mcp <service> <action>
```

### 3.1 服务

- `gsc`
  - project dir: `/Users/celeste/Documents/GitHub/google-search-console-mcp`
  - session: `mcp-gsc`
  - run cmd: `uv run python -m google_search_console_mcp.server`

- `ads`
  - project dir: `/Users/celeste/Documents/GitHub/google-ads-mcp`
  - session: `mcp-ads`
  - run cmd: `uv run python -m google_ads_mcp.server`

### 3.2 动作

- `start`
  如果 tmux session 不存在，则后台启动；如果已存在，则直接提示已运行

- `stop`
  如果 session 存在则杀掉；不存在则提示未运行

- `restart`
  顺序执行 `stop` 再 `start`

- `status`
  显示服务名、session 名、项目路径、运行状态

- `logs`
  直接 `tmux attach -t <session>`

## 4. 行为细节

### 4.1 start

底层执行模型：

```bash
tmux new-session -d -s <session> 'cd <project_dir> && <run_cmd>'
```

### 4.2 stop

底层执行模型：

```bash
tmux kill-session -t <session>
```

### 4.3 status

通过 `tmux has-session -t <session>` 判断是否存活，并输出一行稳定文本。

### 4.4 logs

第一版直接 attach 到 tmux 会话，不做额外日志缓冲层。

## 5. 为什么这样设计

### 5.1 现象层

你不想每次都：

- 开新终端
- `cd` 到项目目录
- 手动输长命令

你要的是一句短命令把 MCP 服务拉起来或停掉。

### 5.2 本质层

真正要管理的不是“命令”，而是：

- 服务名
- tmux session 名
- 项目路径
- 后台运行命令

所以正确抽象不是在 `.zshrc` 里堆一堆 alias，而是一个统一调度函数。

### 5.3 哲学层

`.zshrc` 应该像入口大厅，不该像机房。  
把逻辑塞进 `.zshrc` 是把配置和行为搅成一团。  
好的设计是：

- `.zshrc` 只负责接线
- `mcp.sh` 负责行为

## 6. 明确不做

- 不做动态服务注册
- 不做 `mcp all start`
- 不做后台健康检查
- 不做自动重启
- 不做开机自启
- 不做端口冲突探测
- 不做日志轮转

这些都属于下一层运维能力，不是第一版 shell 管理器的职责。
