# Python API 开发参考

`serial_port.py` 提供三个类的 Python API，可在代码中直接导入使用。

## 模块结构

```
scripts/
├── usart_serial_cli.py   # 命令行入口 —— SerialCLI 类 + main()
└── serial_port.py        # 核心业务层 —— SerialConfig / PortScanner / SerialPort
```

两类职责完全分离，`usart_serial_cli.py` 只负责参数解析与输出格式化，
`serial_port.py` 负责所有 pyserial 交互逻辑。

## 类说明

| 类 | 职责 |
|----|------|
| `SerialConfig` | 串口参数数据类，校验用户输入并映射为 pyserial 常量 |
| `PortScanner` | 系统串口扫描与连通性检测 |
| `SerialPort` | 串口连接上下文管理器，支持文本/十六进制读写 |

## 使用示例

### 扫描串口

```python
from serial_port import PortScanner

# 列出所有串口
ports = PortScanner.list(verbose=True)

# 检查指定串口
PortScanner.check("COM3", baudrate=115200)
```

### 建立连接并收发

```python
from serial_port import SerialConfig, SerialPort

config = SerialConfig.from_args("COM3", baudrate=115200)

with SerialPort(config) as sp:
    # 发送数据
    sp.write("AT\r\n")
    # 读取响应（按行）
    response = sp.read_line()
    print(response.decode())

    # 发送十六进制数据
    sp.write("A5 5A 01 02", fmt="hex")

    # 读取缓冲区所有可用数据
    data = sp.read_available()
```

### SerialConfig 直接构造

```python
from serial_port import SerialConfig

config = SerialConfig(
    port="COM3",
    baudrate=115200,
    timeout=2.0,
)
```

## 代码规范

- 所有注释为中文，docstring 使用 reStructuredText 风格
- 遵循 PEP 8 规范
- 依赖 pyserial (>=3.5)
