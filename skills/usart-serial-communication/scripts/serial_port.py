#!/usr/bin/env python3
"""串口核心模块 —— 提供串口配置、端口扫描与数据收发的类封装。

该模块作为 USART 串口通讯技能的基础层，向上层 CLI 暴露三个主要类：

- :class:`SerialConfig` —— 串口参数数据类，负责校验与映射用户输入
- :class:`PortScanner`  —— 系统串口列表扫描与连通性检测
- :class:`SerialPort`   —— 串口连接、读/写操作的上下文管理器

所有中文注释遵循PEP 8规范，docstring使用reStructuredText 风格。

依赖：
    pyserial (>=3.5): ``pip install pyserial``
"""

from __future__ import annotations

import sys as _sys
from dataclasses import dataclass, field
from typing import Optional

import serial
import serial.tools.list_ports

try:
    from serial.tools import list_ports_common
except ImportError:
    list_ports_common = None  # type: ignore[assignment]

_DEFAULT_DATA_BITS: int = 8
_DEFAULT_STOP_BITS: float = 1.0
_DEFAULT_PARITY: str = "N"
_DEFAULT_TIMEOUT: float = 1.0
_DEFAULT_FLOW_CTRL: str = "none"
_DEFAULT_BAUDRATE: int = 115200

# 校验位映射
_PARITY_MAP: dict[str, str] = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
    "M": serial.PARITY_MARK,
    "S": serial.PARITY_SPACE,
}

# 停止位映射
_STOP_BITS_MAP: dict[str, float] = {
    "1": serial.STOPBITS_ONE,
    "1.5": serial.STOPBITS_ONE_POINT_FIVE,
    "2": serial.STOPBITS_TWO,
}

# 数据位映射
_DATA_BITS_MAP: dict[str, int] = {
    "5": serial.FIVEBITS,
    "6": serial.SIXBITS,
    "7": serial.SEVENBITS,
    "8": serial.EIGHTBITS,
}

# 流控映射
_FLOW_CTRL_MAP: dict[str, bool] = {
    "none": False,
    "rtscts": True,
}


@dataclass
class SerialConfig:
    """串口通讯参数配置数据类。

    负责校验用户传入的字符串形式参数，并映射为 pyserial 所需的底层常量。
    所有字段均提供合理默认值，未显式赋值时按最常用场景（9600-8-N-1）初始化。

    Attributes:
        port: 串口设备名，如 ``COM3`` 或 ``/dev/ttyUSB0``。
        baudrate: 波特率，默认 9600。
        data_bits: 数据位（5/6/7/8），使用 pyserial 常量。
        stop_bits: 停止位（1/1.5/2），使用 pyserial 常量。
        parity: 校验位，使用 pyserial 常量。
        timeout: 读写超时，单位秒。
        flow_control: 是否启用 RTS/CTS 硬件流控。
    """

    port: str
    baudrate: int = _DEFAULT_BAUDRATE
    data_bits: int = serial.EIGHTBITS
    stop_bits: float = serial.STOPBITS_ONE
    parity: str = serial.PARITY_NONE
    timeout: float = _DEFAULT_TIMEOUT
    flow_control: bool = False

    @classmethod
    def from_args(
            cls,
            port: str,
            *,
            baudrate: int = _DEFAULT_BAUDRATE,
            data_bits: str = "8",
            stop_bits: str = "1",
            parity: str = "N",
            timeout: float = _DEFAULT_TIMEOUT,
            flow_control: str = "none",
    ) -> "SerialConfig":
        """从命令行参数创建配置实例，自动完成校验与映射。

        Args:
            port: 串口设备名。
            baudrate: 波特率数值。
            data_bits: 数据位字符串（``"5"`` / ``"6"`` / ``"7"`` / ``"8"``）。
            stop_bits: 停止位字符串（``"1"`` / ``"1.5"`` / ``"2"``）。
            parity: 校验位字符串（``"N"`` / ``"E"`` / ``"O"`` / ``"M"`` / ``"S"``）。
            timeout: 超时秒数。
            flow_control: 流控字符串（``"none"`` / ``"rtscts"``）。

        Returns:
            已映射为 pyserial 常量的 :class:`SerialConfig` 实例。

        Raises:
            KeyError: 当任一字符串参数为非法值时抛出。
        """
        return cls(
            port=port,
            baudrate=baudrate,
            data_bits=_map_data_bits(data_bits),
            stop_bits=_map_stop_bits(stop_bits),
            parity=_map_parity(parity),
            timeout=timeout,
            flow_control=_map_flow_control(flow_control),
        )

    @property
    def summary(self) -> str:
        """返回人类可读的配置摘要字符串。"""
        return (
            f"{self.port} @ {self.baudrate} baud, "
            f"数据位={_DATA_BITS_REV[self.data_bits]}, "
            f"停止位={_STOP_BITS_REV[self.stop_bits]}, "
            f"校验={_PARITY_REV[self.parity]}, "
            f"流控={'RTS/CTS' if self.flow_control else '无'}"
        )


_DATA_BITS_REV: dict[int, str] = {v: k for k, v in _DATA_BITS_MAP.items()}
_STOP_BITS_REV: dict[float, str] = {v: k for k, v in _STOP_BITS_MAP.items()}
_PARITY_REV: dict[str, str] = {v: k for k, v in _PARITY_MAP.items()}


def _map_parity(raw: str) -> str:
    """将用户输入的校验位字符转为 pyserial 常量。

    Args:
        raw: 校验位字符串（``N`` / ``E`` / ``O`` / ``M`` / ``S``）。

    Returns:
        pyserial 校验常量。

    Raises:
        KeyError: 输入值不在合法范围内。
    """
    try:
        return _PARITY_MAP[raw.upper()]
    except KeyError:
        raise KeyError(f"无效的校验位 '{raw}'，合法值: {'/'.join(_PARITY_MAP)}") from None


def _map_stop_bits(raw: str) -> float:
    """将用户输入的停止位字符串转为 pyserial 常量。

    Args:
        raw: 停止位字符串（``"1"`` / ``"1.5"`` / ``"2"``）。

    Returns:
        pyserial 停止位常量。

    Raises:
        KeyError: 输入值不在合法范围内。
    """
    try:
        return _STOP_BITS_MAP[raw]
    except KeyError:
        raise KeyError(f"无效的停止位 '{raw}'，合法值: {'/'.join(_STOP_BITS_MAP)}") from None


def _map_data_bits(raw: str) -> int:
    """将用户输入的数据位字符串转为 pyserial 常量。

    Args:
        raw: 数据位字符串（``"5"`` / ``"6"`` / ``"7"`` / ``"8"``）。

    Returns:
        pyserial 数据位常量。

    Raises:
        KeyError: 输入值不在合法范围内。
    """
    try:
        return _DATA_BITS_MAP[raw]
    except KeyError:
        raise KeyError(f"无效的数据位 '{raw}'，合法值: {'/'.join(_DATA_BITS_MAP)}") from None


def _map_flow_control(raw: str) -> bool:
    """将用户输入的流控字符串转为布尔值。

    Args:
        raw: 流控字符串（``"none"`` / ``"rtscts"``）。

    Returns:
        ``True`` 表示启用 RTS/CTS 硬件流控。
    """
    raw = raw.lower()
    if raw not in _FLOW_CTRL_MAP:
        raise KeyError(f"无效的流控 '{raw}'，合法值: {'/'.join(_FLOW_CTRL_MAP)}") from None
    return _FLOW_CTRL_MAP[raw]


class PortScanner:
    """系统串口扫描器 —— 枚举可用端口并检测连通性。

    基于 pyserial 的 :func:`serial.tools.list_ports.comports` 枚举串口（通过 SetupAPI），
    在 Windows 上若 SetupAPI 无结果则回退至注册表
    ``HKLM\\HARDWARE\\DEVICEMAP\\SERIALCOMM`` 扫描，以兼容 com0com 等虚拟串口驱动。

    Examples:
        >>> PortScanner.list()
        >>> PortScanner.check("COM3")
    """

    @staticmethod
    def list(*, verbose: bool = False) -> list[str]:
        """扫描并打印当前系统中所有可用的串口设备。

        优先使用 pyserial 枚举，Windows 上无结果时回退注册表扫描。

        Args:
            verbose: 为 ``True`` 时额外输出 VID/PID、厂商名、硬件 ID 等信息。

        Returns:
            发现的串口设备名列表（如 ``["COM1", "COM2"]``）。

        Raises:
            RuntimeError: 未安装 pyserial 库时抛出。
        """
        try:
            ports = list(serial.tools.list_ports.comports())
        except ImportError:
            raise RuntimeError(
                "未安装 pyserial 库，请执行: pip install pyserial"
            ) from None

        # Windows 上 SetupAPI 可能漏掉虚拟串口（如 com0com），回退注册表
        if not ports and _sys.platform == "win32":
            ports = PortScanner._win_registry_ports()

        if not ports:
            print("未发现任何串口设备。")
            return []

        print(f"发现 {len(ports)} 个串口:\n")
        names: list[str] = []
        for p in sorted(ports, key=lambda x: x.device):
            names.append(p.device)
            print(f"  {p.device}")
            if verbose:
                print(f"    描述   : {p.description or 'N/A'}")
                print(f"    厂商   : {p.manufacturer or 'N/A'}")
                if getattr(p, "vid", None) is not None:
                    print(f"    VID:PID: {p.vid:04X}:{p.pid:04X}")
                print(f"    HWID   : {p.hwid or 'N/A'}")
                print()
        return names

    @staticmethod
    def check(
            port: str,
            *,
            baudrate: int = _DEFAULT_BAUDRATE,
            timeout: float = _DEFAULT_TIMEOUT,
    ) -> int:
        """检测指定串口是否存在并可正常打开。

        先枚举确认端口存在，再尝试打开/关闭以验证连通性。

        Args:
            port: 串口设备名。
            baudrate: 测试用波特率。
            timeout: 测试用超时秒数。

        Returns:
            0 表示端口可用；1 表示端口不存在或无法打开。
        """
        if not PortScanner._exists(port):
            print(f"[错误] 端口 '{port}' 不存在，请用 'list' 查看可用串口。")
            return 1

        print(f"端口            : {port}")
        print(f"测试波特率      : {baudrate}")
        print(f"测试超时        : {timeout} s")
        print()
        try:
            ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            ser.close()
            print(f"[成功] 端口 '{port}' 打开/关闭正常。")
            return 0
        except serial.SerialException as exc:
            print(f"[失败] 无法打开 '{port}': {exc}")
            return 1

    @staticmethod
    def _exists(port: str) -> bool:
        """判断 *port* 是否存在于系统中。

        Windows 上依次检查 pyserial 枚举结果与注册表。
        """
        try:
            if any(p.device == port for p in serial.tools.list_ports.comports()):
                return True
        except ImportError:
            pass

        if _sys.platform == "win32":
            reg_ports = PortScanner._win_registry_ports()
            if any(p.device == port for p in reg_ports):
                return True

        return False

    @staticmethod
    def _win_registry_ports() -> list:
        """从 Windows 注册表读取串口列表（回退方案）。

        读取 ``HKLM\\HARDWARE\\DEVICEMAP\\SERIALCOMM`` 键下的所有值，
        返回与 :func:`comports` 兼容的 ``ListPortInfo`` 对象列表。

        Returns:
            注册表中记录的串口设备列表，无权限时返回空列表。
        """
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DEVICEMAP\SERIALCOMM",
            )
        except OSError:
            return []

        results = []
        index = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, index)
                info = list_ports_common.ListPortInfo(value)  # type: ignore[misc]
                info.description = name
                info.hwid = name
                results.append(info)
                index += 1
            except OSError:
                break
        winreg.CloseKey(key)
        return results


class SerialPort:
    """串口连接与数据收发类。

    封装 pyserial 的 ``Serial`` 对象，提供安全的上下文管理器接口，
    确保退出时自动关闭串口。支持文本和十六进制两种数据格式。

    Usage::

        with SerialPort(SerialConfig("COM3", 115200)) as sp:
            data = sp.read_line()
            sp.write("AT\\r\\n")
    """

    def __init__(self, config: SerialConfig) -> None:
        """初始化串口连接。

        Args:
            config: 已校验的 :class:`SerialConfig` 实例。
        """
        self._config: SerialConfig = config
        self._serial: Optional[serial.Serial] = None

    def __enter__(self) -> "SerialPort":
        """进入运行时上下文，自动打开串口。"""
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        """退出运行时上下文，自动关闭串口。"""
        self.close()

    def open(self) -> None:
        """打开串口连接。

        Raises:
            serial.SerialException: 串口不可用或无权限时抛出。
        """
        if self._serial is not None and self._serial.is_open:
            return
        self._serial = serial.Serial(
            port=self._config.port,
            baudrate=self._config.baudrate,
            timeout=self._config.timeout,
            bytesize=self._config.data_bits,
            stopbits=self._config.stop_bits,
            parity=self._config.parity,
            rtscts=self._config.flow_control,
        )

    def close(self) -> None:
        """关闭串口连接（安全关闭，已关闭状态下无操作）。"""
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None

    def read_line(self) -> bytes:
        """读取一行数据（以换行符为界）。

        Returns:
            接收到的原始字节数据，超时返回空字节串。
        """
        self._ensure_open()
        return self._serial.readline()  # type: ignore[union-attr]

    def read_available(self) -> bytes:
        """读取缓冲区中当前所有可用的字节（非阻塞）。

        先通过 :attr:`in_waiting` 查询可读字节数，再一次性读取，
        避免因等待换行符导致的阻塞问题，兼容无换行符的数据流。

        Returns:
            缓冲区中全部可读字节，无数据时返回空字节串。
        """
        self._ensure_open()
        waiting: int = self._serial.in_waiting  # type: ignore[union-attr]
        if waiting == 0:
            # 无可用数据，尝试读取 1 字节触发超时等待
            return self._serial.read(1)  # type: ignore[union-attr]
        return self._serial.read(waiting)  # type: ignore[union-attr]

    def read_bytes(self, size: int = 1) -> bytes:
        """读取指定字节数。

        Args:
            size: 期望读取的字节数。

        Returns:
            接收到的原始字节数据，可能少于 *size*。
        """
        self._ensure_open()
        return self._serial.read(size)  # type: ignore[union-attr]

    def write(self, data: str, *, fmt: str = "text", append_newline: bool = True):
        """向串口发送数据。

        Args:
            data: 待发送的数据字符串。文本模式下为普通字符串，十六进制模式下为 hex 字符串。
            fmt: 数据格式 —— ``"text"`` 或 ``"hex"``。
            append_newline: 文本模式下是否在末尾追加 ``\\n``（十六进制模式忽略）。

        Returns:
            实际写入的字节数。

        Raises:
            ValueError: *fmt* 非法或 *data* 在 hex 模式下无效。
            RuntimeError: 串口未打开。
        """
        self._ensure_open()
        payload = self._encode(data, fmt=fmt, append_newline=append_newline)
        written = self._serial.write(payload)  # type: ignore[union-attr]
        self._serial.flush()  # type: ignore[union-attr]
        return written

    def _ensure_open(self) -> None:
        """确保串口处于打开状态，否则抛出运行时错误。"""
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("串口未打开，请先调用 open() 或使用 with 语句。")

    @staticmethod
    def _encode(data: str, *, fmt: str, append_newline: bool) -> bytes:
        """将字符串数据编码为待发送的字节串。

        Args:
            data: 原始数据字符串。
            fmt: ``"text"`` 或 ``"hex"``。
            append_newline: 是否追加换行。

        Returns:
            编码后的字节串。
        """
        if fmt not in ("text", "hex"):
            raise ValueError(f"不支持的数据格式 '{fmt}'，请使用 'text' 或 'hex'。")

        if fmt == "hex":
            cleaned = data.replace(" ", "")
            try:
                return bytes.fromhex(cleaned)
            except ValueError:
                raise ValueError(
                    f"无效的十六进制数据: '{data}'，请确保仅包含 0-9、A-F 及可选空格。"
                ) from None

        payload = data.encode("utf-8")
        if append_newline:
            payload += b"\n"
        return payload

    @property
    def is_open(self) -> bool:
        """返回串口当前是否处于打开状态。"""
        return self._serial is not None and self._serial.is_open

    @property
    def in_waiting(self) -> int:
        """返回接收缓冲区中等待读取的字节数。"""
        self._ensure_open()
        return self._serial.in_waiting  # type: ignore[union-attr]

    @property
    def config(self) -> SerialConfig:
        """返回只读的串口配置对象。"""
        return self._config
