---
name: usart-serial-communication
description: >-
  提供完整的USART/串口通讯能力，包括扫描串口、参数配置、数据收发、格式转换与端口诊断。
  当用户需要与嵌入式设备、单片机、传感器等通过串口通讯，或提及串口、COM口、TTL、
  RS232、RS485、USART、UART 时应主动使用此技能。即使用户未明确提到"串口"，
  只要涉及硬件调试、固件通讯、传感器数据采集等场景也应触发。
---

# USART 串口通讯

通过 `scripts/usart_serial_cli.py` 命令行工具完成所有串口操作。

## 目录结构

```
usart-serial-communication/
├── SKILL.md                  # 技能说明（本文件）
├── scripts/
│   ├── usart_serial_cli.py  # 命令行入口 —— SerialCLI
│   └── serial_port.py       # 核心库 —— SerialConfig / PortScanner / SerialPort
└── references/
    └── code.md              # Python API 二次开发参考
```

如需在代码中直接调用 Python API，阅读 `references/code.md`。

## 依赖安装

```bash
pip install pyserial
```

## 命令概览

| 命令 | 功能 | 示例 |
|------|------|------|
| `list` | 列出所有可用串口 | `python scripts/usart_serial_cli.py list` |
| `check` | 检查串口是否可打开 | `python scripts/usart_serial_cli.py check COM3` |
| `read` | 读取串口数据 | `python scripts/usart_serial_cli.py read COM3 -b 115200 -T 5` |
| `write` | 向串口发送数据 | `python scripts/usart_serial_cli.py write COM3 -d "AT\r\n"` |

## 常用选项

- `-b, --baudrate` — 波特率，默认 115200
- `-t, --timeout` — 超时（秒），默认 1.0
- `--data-bits` — 数据位（5/6/7/8），默认 8
- `--stop-bits` — 停止位（1/1.5/2），默认 1
- `-p, --parity` — 校验位（N/E/O/M/S），默认 N
- `-f, --flow-control` — 流控（none/rtscts），默认 none

### read 专属

- `-T, --duration` — 读取持续时间（秒），0 为持续直到 Ctrl+C，默认 0
- `--format text|hex` — 输出格式，默认 text
- `--raw` — 原始字节输出（适合管道/重定向）

### write 专属

- `-d, --data` — 待发送数据（文本或十六进制字符串）
- `--format text|hex` — 数据格式，默认 text
- `-n, --no-newline` — 不追加换行符

## 使用示例

### 扫描与检测

```bash
python scripts/usart_serial_cli.py list
python scripts/usart_serial_cli.py list --verbose
python scripts/usart_serial_cli.py check COM3 -b 115200
```

### 读取数据

```bash
# 持续读取，Ctrl+C 停止
python scripts/usart_serial_cli.py read COM3 -b 115200

# 读取 5 秒后自动退出
python scripts/usart_serial_cli.py read COM3 -b 115200 -T 5

# 十六进制模式
python scripts/usart_serial_cli.py read COM3 -b 115200 --format hex

# 原始输出（管道/重定向）
python scripts/usart_serial_cli.py read COM3 --raw > output.bin
```

### 发送数据

```bash
# 发送文本（自动追加换行）
python scripts/usart_serial_cli.py write COM3 -d "AT+GMR"

# 发送十六进制（可带空格）
python scripts/usart_serial_cli.py write COM3 -d "A5 5A 01 02" --format hex

# 不追加换行
python scripts/usart_serial_cli.py write COM3 -d "data" -n
```

## 典型工作流

1. **`list`** — 确认目标串口已连接
2. **`check`** — 验证串口可正常打开
3. **`read` / `write`** — 执行实际通讯


## 执行流程
1. 确定串口号与连接方式, 对应通讯的波特率、数据位、停止位、校验位等参数, 用户不输入则使用默认值, 对于`read`操作, 默认持续读取15秒并提醒用户延迟时间
2. 使用`check`验证串口是否可正常打开
3. 执行对应的命令，并返回运行结果


## 注意事项

- Windows 串口格式 `COMx`，Linux 为 `/dev/ttyUSBx` 或 `/dev/ttySx`
- 错误信息输出到 stderr，成功信息输出到 stdout
- 十六进制数据可带空格，脚本自动去除
