#!/usr/bin/env python3
"""USART 串口通讯命令行工具。

提供 ``list``、``check``、``read``、``write`` 四个子命令，
基于 :mod:`serial_port` 模块中的 :class:`SerialConfig`、:class:`PortScanner`、
:class:`SerialPort` 实现全部串口操作。

用法示例::

    python usart_serial_cli.py list
    python usart_serial_cli.py check COM3
    python usart_serial_cli.py read COM3 -b 115200
    python usart_serial_cli.py write COM3 -d "AT\\r\\n"
    python usart_serial_cli.py read COM3 --format hex
    python usart_serial_cli.py write COM3 -d "A55A" --format hex

所有中文注释遵循PEP 8规范，docstring使用reStructuredText风格。
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional, Sequence
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from serial_port import PortScanner, SerialConfig, SerialPort

_DEFAULT_DATA_BITS: str = "8"
_DEFAULT_STOP_BITS: str = "1"
_DEFAULT_PARITY: str = "N"
_DEFAULT_TIMEOUT: float = 1.0
_DEFAULT_FLOW_CTRL: str = "none"
_DEFAULT_BAUDRATE: int = 115200


def _add_serial_args(parser: argparse.ArgumentParser) -> None:
    """向 *parser* 注册串口通用命令行参数。"""
    parser.add_argument("port", help="串口设备名（如 COM3 或 /dev/ttyUSB0）。")
    parser.add_argument(
        "-b", "--baudrate", type=int, default=_DEFAULT_BAUDRATE,
        help=f"波特率（默认: {_DEFAULT_BAUDRATE}）。",
    )
    parser.add_argument(
        "-t", "--timeout", type=float, default=_DEFAULT_TIMEOUT,
        help=f"读写超时秒数（默认: {_DEFAULT_TIMEOUT}）。",
    )
    parser.add_argument(
        "--data-bits", type=str, default=_DEFAULT_DATA_BITS,
        choices=["5", "6", "7", "8"],
        help=f"数据位（默认: {_DEFAULT_DATA_BITS}）。",
    )
    parser.add_argument(
        "--stop-bits", type=str, default=_DEFAULT_STOP_BITS,
        choices=["1", "1.5", "2"],
        help=f"停止位（默认: {_DEFAULT_STOP_BITS}）。",
    )
    parser.add_argument(
        "-p", "--parity", type=str, default=_DEFAULT_PARITY,
        choices=["N", "E", "O", "M", "S"],
        help=f"校验位: N=无 E=偶 O=奇 M=标记 S=空格（默认: {_DEFAULT_PARITY}）。",
    )
    parser.add_argument(
        "-f", "--flow-control", type=str, default=_DEFAULT_FLOW_CTRL,
        choices=["none", "rtscts"],
        help=f"流控（默认: {_DEFAULT_FLOW_CTRL}）。",
    )


class SerialCLI:
    """USART 串口命令行工具主类。

    负责解析命令行参数并调度对应的串口操作。
    高内聚、低耦合的设计使得业务逻辑 (:mod:`serial_port`) 与 CLI 层完全分离。

    Usage::

        cli = SerialCLI()
        sys.exit(cli.run(["read", "COM3", "-b", "115200"]))
    """

    @staticmethod
    def cmd_list(*, verbose: bool = False) -> int:
        """执行 ``list`` 子命令 —— 枚举系统串口。

        Args:
            verbose: 为 ``True`` 时打印详细信息（VID/PID、厂商等）。

        Returns:
            始终返回 0。
        """
        PortScanner.list(verbose=verbose)
        return 0

    @staticmethod
    def cmd_check(port: str, *, baudrate: int = _DEFAULT_BAUDRATE,
                  timeout: float = _DEFAULT_TIMEOUT) -> int:
        """执行 ``check`` 子命令 —— 检测串口连通性。

        Args:
            port: 串口设备名。
            baudrate: 测试用波特率。
            timeout: 测试用超时秒数。

        Returns:
            0 表示可用，1 表示不可用。
        """
        return PortScanner.check(port, baudrate=baudrate, timeout=timeout)

    @staticmethod
    def cmd_read(port: str,
                 *,
                 baudrate: int = _DEFAULT_BAUDRATE,
                 timeout: float = _DEFAULT_TIMEOUT,
                 data_bits: str = _DEFAULT_DATA_BITS,
                 stop_bits: str = _DEFAULT_STOP_BITS,
                 parity: str = _DEFAULT_PARITY,
                 flow_control: str = _DEFAULT_FLOW_CTRL,
                 fmt: str = "text",
                 raw: bool = False,
                 duration: float = 0.0) -> int:
        """执行 ``read`` 子命令 —— 读取串口数据。

        Args:
            port: 串口设备名。
            baudrate: 波特率。
            timeout: 单次读取超时秒数（控制 readline / read_available 等待时长）。
            data_bits: 数据位字符串。
            stop_bits: 停止位字符串。
            parity: 校验位字符串。
            flow_control: 流控字符串。
            fmt: 输出格式，``"text"`` 或 ``"hex"``。
            raw: 为 ``True`` 时直接输出原始字节到 stdout（适合管道）。
            duration: 读取总时长（秒），0 表示持续读取直到 Ctrl+C 中断。

        Returns:
            0 正常退出，1 串口打开失败，2 用户 Ctrl+C 中断。
        """
        if fmt not in ("text", "hex"):
            print(f"[错误] 不支持的格式 '{fmt}'，请使用 'text' 或 'hex'。", file=sys.stderr)
            return 1

        try:
            config = SerialConfig.from_args(
                port, baudrate=baudrate, timeout=timeout,
                data_bits=data_bits, stop_bits=stop_bits,
                parity=parity, flow_control=flow_control,
            )
        except KeyError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            return 1

        try:
            with SerialPort(config) as sp:
                if not raw:
                    print(f"正在监听 {config.summary}")
                    if duration:
                        print(f"持续时间: {duration} 秒")
                    else:
                        print("Ctrl+C 停止")
                    print("-" * 50)
                return SerialCLI._read_loop(sp, fmt=fmt, raw=raw, duration=duration)
        except serial_exception() as exc:
            print(f"[错误] 无法打开 '{port}': {exc}", file=sys.stderr)
            return 1

    @staticmethod
    def cmd_write(port: str,
                  data: str,
                  *,
                  baudrate: int = _DEFAULT_BAUDRATE,
                  timeout: float = _DEFAULT_TIMEOUT,
                  data_bits: str = _DEFAULT_DATA_BITS,
                  stop_bits: str = _DEFAULT_STOP_BITS,
                  parity: str = _DEFAULT_PARITY,
                  flow_control: str = _DEFAULT_FLOW_CTRL,
                  fmt: str = "text",
                  no_newline: bool = False) -> int:
        """执行 ``write`` 子命令 —— 向串口发送数据。

        Args:
            port: 串口设备名。
            data: 待发送的数据（文本或十六进制字符串）。
            baudrate: 波特率。
            timeout: 超时秒数。
            data_bits: 数据位字符串。
            stop_bits: 停止位字符串。
            parity: 校验位字符串。
            flow_control: 流控字符串。
            fmt: 数据格式，``"text"`` 或 ``"hex"``。
            no_newline: 为 ``True`` 时不追加换行符。

        Returns:
            0 发送成功，1 失败。
        """
        if fmt not in ("text", "hex"):
            print(f"[错误] 不支持的格式 '{fmt}'，请使用 'text' 或 'hex'。", file=sys.stderr)
            return 1

        try:
            config = SerialConfig.from_args(
                port, baudrate=baudrate, timeout=timeout,
                data_bits=data_bits, stop_bits=stop_bits,
                parity=parity, flow_control=flow_control,
            )
        except KeyError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            return 1

        try:
            with SerialPort(config) as sp:
                written = sp.write(data, fmt=fmt, append_newline=not no_newline)
                print(f"[成功] 已向 {config.summary} 发送 {written} 字节。")
                return 0
        except serial_exception() as exc:
            print(f"[错误] 无法打开 '{port}': {exc}", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(f"[错误] {exc}", file=sys.stderr)
            return 1

    @staticmethod
    def _read_loop(sp: SerialPort, *, fmt: str, raw: bool,
                   duration: float = 0.0) -> int:
        """串口数据读取循环。

        使用 :meth:`SerialPort.read_available` 读取缓冲区中所有可用字节，
        不依赖换行符，兼容任意格式的数据流。

        Args:
            sp: 已打开的 :class:`SerialPort` 实例。
            fmt: 输出格式。
            raw: 是否原始输出。
            duration: 总持续时间（秒），0 表示无限循环。

        Returns:
            2 表示 Ctrl+C 中断，0 表示超时结束或其他退出。
        """
        start = time.monotonic()
        try:
            while True:
                data = sp.read_available()
                if data:
                    if raw:
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                    elif fmt == "hex":
                        print(data.hex(" ").upper())
                    else:
                        print(data.decode("utf-8", errors="replace"), end="")
                        sys.stdout.flush()
                elif duration and time.monotonic() - start >= duration:
                    if not raw:
                        print("\n[停止] 读取时间到。")
                    return 0
        except KeyboardInterrupt:
            if not raw:
                print("\n[停止] 用户中断。")
            return 2
        return 0

    def run(self, argv: Optional[Sequence[str]] = None) -> int:
        """解析命令行参数并执行对应子命令。

        Args:
            argv: 命令行参数列表，默认使用 :data:`sys.argv`。

        Returns:
            进程退出码（0 成功，非零失败）。
        """
        if argv is None:
            argv = sys.argv[1:]

        parser = self._build_parser()
        args = parser.parse_args(argv)
        cmd: str = args.command

        if cmd == "list":
            return self.cmd_list(verbose=getattr(args, "verbose", False))

        if cmd == "check":
            return self.cmd_check(args.port, baudrate=args.baudrate,
                                  timeout=args.timeout)

        if cmd == "read":
            return self.cmd_read(
                args.port,
                baudrate=args.baudrate,
                timeout=args.timeout,
                data_bits=args.data_bits,
                stop_bits=args.stop_bits,
                parity=args.parity,
                flow_control=args.flow_control,
                fmt=args.format,
                raw=getattr(args, "raw", False),
                duration=getattr(args, "duration", 0.0),
            )

        if cmd == "write":
            return self.cmd_write(
                args.port,
                args.data,
                baudrate=args.baudrate,
                timeout=args.timeout,
                data_bits=args.data_bits,
                stop_bits=args.stop_bits,
                parity=args.parity,
                flow_control=args.flow_control,
                fmt=args.format,
                no_newline=getattr(args, "no_newline", False),
            )

        # 理论上不会到达（required subparser 保证）
        parser.print_help()
        return 1

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """构建完整的命令行解析器。

        Returns:
            配置好的 :class:`argparse.ArgumentParser` 实例。
        """
        parser = argparse.ArgumentParser(
            prog="usart_serial_cli",
            description="USART 串口通讯命令行工具",
        )
        parser.add_argument(
            "--version", action="version", version="%(prog)s 1.0.0",
        )
        sub = parser.add_subparsers(dest="command", required=True)

        # ---- list ----
        lp = sub.add_parser("list", help="列出可用串口。")
        lp.add_argument("-v", "--verbose", action="store_true",
                        help="显示详细信息（VID/PID、厂商等）。")

        # ---- check ----
        cp = sub.add_parser("check", help="检测串口是否可用。")
        cp.add_argument("port", help="串口设备名（如 COM3）。")
        cp.add_argument("-b", "--baudrate", type=int, default=_DEFAULT_BAUDRATE,
                        help=f"测试波特率（默认: {_DEFAULT_BAUDRATE}）。")
        cp.add_argument("-t", "--timeout", type=float, default=_DEFAULT_TIMEOUT,
                        help=f"超时秒数（默认: {_DEFAULT_TIMEOUT}）。")

        # ---- read ----
        rp = sub.add_parser("read", help="读取串口数据。")
        _add_serial_args(rp)
        rp.add_argument("--format", type=str, choices=("text", "hex"), default="text",
                        help="输出格式: text（UTF-8）或 hex（大写十六进制）。默认: text。")
        rp.add_argument("--raw", action="store_true",
                        help="直接输出原始字节到 stdout（适合管道/重定向）。")
        rp.add_argument("-T", "--duration", type=float, default=0.0,
                        help="读取持续时间（秒），0 表示持续读取直到 Ctrl+C。默认: 0。")

        # ---- write ----
        wp = sub.add_parser("write", help="向串口发送数据。")
        _add_serial_args(wp)
        wp.add_argument("-d", "--data", type=str, required=True,
                        help="待发送数据（文本或十六进制字符串）。")
        wp.add_argument("--format", type=str, choices=("text", "hex"), default="text",
                        help="数据格式: text 或 hex。默认: text。")
        wp.add_argument("-n", "--no-newline", action="store_true",
                        help="不追加换行符（仅文本模式有效）。")

        return parser


def serial_exception():
    """延迟引用 :exc:`serial.SerialException`，避免顶层导入错误。"""
    import serial as _serial
    return _serial.SerialException


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主入口函数。

    Args:
        argv: 命令行参数，默认 :data:`sys.argv`。

    Returns:
        进程退出码。
    """
    cli = SerialCLI()
    return cli.run(argv)


if __name__ == "__main__":
    sys.exit(main())
