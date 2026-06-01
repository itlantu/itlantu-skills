---
name: usart-serial-communication
description: >-
  提供完整的USART/串口通讯能力，支持扫描串口、参数配置、数据收发、格式转换与端口诊断。
  当用户需要与嵌入式设备、单片机、传感器等通过串口通讯，或提及串口、COM口、TTL、
  RS232、RS485、USART、UART 时自动触发。
---

# USART 串口通讯

通过 `scripts/usart_serial_cli.py` 命令行工具完成所有串口操作。

## 模块结构

```
scripts/
├── usart_serial_cli.py   # 命令行入口 —— SerialCLI 类 + main()
└── serial_port.py        # 核心业务层 —— SerialConfig / PortScanner / SerialPort
```

- **SerialConfig** — 串口参数数据类，校验用户输入并映射为 pyserial 常量
- **PortScanner** — 系统串口扫描与连通性检测
- **SerialPort** — 串口连接上下文管理器，支持文本/十六进制读写
- **SerialCLI** — 命令行解析与子命令调度

两类职责完全分离，`usart_serial_cli.py` 只负责参数解析与输出格式化，
`serial_port.py` 负责所有 pyserial 交互逻辑。

## 依赖安装

```bash
pip install pyserial
```

## 命令概览

| 命令 | 功能 | 示例 |
|------|------|------|
| `list` | 列出系统中所有可用串口 | `python scripts/usart_serial_cli.py list` |
| `check` | 检查指定串口是否可用并测试连通性 | `python scripts/usart_serial_cli.py check COM3` |
| `read` | 持续读取串口数据（Ctrl+C 停止） | `python scripts/usart_serial_cli.py read COM3 -b 115200` |
| `write` | 向串口发送数据 | `python scripts/usart_serial_cli.py write COM3 -d "AT\r\n"` |

## 常用选项

所有串口操作共享以下参数：

- `-b, --baudrate` — 波特率，默认 9600
- `-t, --timeout` — 超时（秒），默认 1.0
- `--data-bits` — 数据位（5/6/7/8），默认 8
- `--stop-bits` — 停止位（1/1.5/2），默认 1
- `-p, --parity` — 校验位（N/E/O/M/S），默认 N
- `-f, --flow-control` — 流控（none/rtscts），默认 none

## 使用示例

### 1. 扫描串口

```bash
python scripts/usart_serial_cli.py list

# 显示详细信息（VID/PID、厂商等）
python scripts/usart_serial_cli.py list --verbose
```

### 2. 检查串口

```bash
python scripts/usart_serial_cli.py check COM3

# 指定波特率检测
python scripts/usart_serial_cli.py check COM8 -b 115200
```

### 3. 读取数据

```bash
# 文本模式读取（默认 UTF-8 解码）
python scripts/usart_serial_cli.py read COM3 -b 115200

# 十六进制模式读取（大写，空格分隔）
python scripts/usart_serial_cli.py read COM3 -b 115200 --format hex

# 原始字节输出（适合管道/重定向）
python scripts/usart_serial_cli.py read COM3 --raw > output.bin
```

### 4. 发送数据

```bash
# 发送文本（自动追加换行）
python scripts/usart_serial_cli.py write COM3 -d "AT+GMR"

# 发送十六进制数据
python scripts/usart_serial_cli.py write COM3 -d "48 65 6C 6C 6F" --format hex

# 不追加换行符
python scripts/usart_serial_cli.py write COM3 -d "data" --no-newline
```

### 5. 在代码中直接使用

```python
from serial_port import SerialConfig, PortScanner, SerialPort

# 扫描串口
ports = PortScanner.list(verbose=True)

# 建立连接并收发
config = SerialConfig.from_args("COM3", baudrate=115200)
with SerialPort(config) as sp:
    sp.write("AT\r\n")
    response = sp.read_line()
    print(response.decode())
```

## 典型工作流

当用户通过自然语言描述串口需求时，提取关键参数后调用脚本：

1. **先 `list`** — 确认目标串口设备已连接
2. **再 `check`** — 验证串口可正常打开
3. **按需 `read` / `write`** — 执行实际通讯

## 注意事项

- Windows 上串口名格式为 `COMx`，Linux 上为 `/dev/ttyUSBx` 或 `/dev/ttySx`
- `read` 命令会持续阻塞，需按 `Ctrl+C` 终止
- 发送十六进制数据时可带空格（脚本自动去除），如 `"A5 5A 01 02"`
- 所有错误信息输出到 stderr，成功信息输出到 stdout，便于脚本集成
- 所有代码注释为中文，docstring 使用 reStructuredText 风格，遵循 PEP 8 规范
