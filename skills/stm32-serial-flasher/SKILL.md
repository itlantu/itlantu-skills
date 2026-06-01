---
name: stm32-serial-flasher
description: "使用STM_32CubeProgrammer_CLI通过UART串口(系统Bootloader)烧录固件,适用于arm-none-eabi-gcc生成的ELF或Bin文件"
---

# STM32串口烧录(UART ISP)

## 工具简介
`STM32_Programmer_CLI`是ST官方提供的命令行烧录工具,支持通过**UART 串口**连接 STM32 芯片内嵌的 Bootloader,完成固件下载与校验。


## 支持的固件格式
推荐使用`.elf`文件(自动解析地址),也可使用`.bin`文件(需配合默认起始地址`0x08000000`)


## 串口设备命名规则
- **Windows**：`COMx`,例如`COM5`
- **Linux**：`/dev/ttyUSBx`,例如`/dev/ttyUSB1`


## 快速示例
```bash
# Windows,COM5,烧录 blink.elf(默认波特率 115200,校验并复位运行)
STM32_Programmer_CLI -c port=COM5 -w blink.elf -v -s

# Linux,串口 /dev/ttyUSB1,自定义波特率 921600
STM32_Programmer_CLI -c port=/dev/ttyUSB1 br=921600 -w firmware.elf -v -s
```

## 工具参数
* 先调用`-c`参数指定连接参数,后续参数根据需要添加

选项|作用
--|--
`-c`|指定连接参数
`port=<PortName>`|指定串口设备路径
`br=<baudrate>`|指定串口波特率, 一般为`115200/921600`, 具体取决于Bootloader的支持
`-w <file>`|指定要烧录的固件文件路径, 可以是`.elf`或`.bin`格式
`-v`|烧录完成后自动校验数据完整性
`-s`|烧录完成后自动启动程序(从 Flash 运行)
`-e all`|(可选)烧录前先全片擦除
`--skipErase`|(可选)跳过扇区擦除(仅用于增量更新)


## 操作步骤
1. `确认工具可用`：若命令行无法直接调用`STM32_Programmer_CLI`,请询问用户安装路径(Windows下典型路径：`C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin`)
2. `确认串口号`：向用户询问串口号, 调用脚本获取当前平台的串口号,确保串口号符合规范,并提醒用户检查硬件连接与BOOT0电平
3. `确认波特率`: 询问用户烧录串口的波特率, 默认为`115200`
4. `确认固件文件`: 在不确定烧录文件的时候询问用户需要烧录的文件路径, 并且保证为`.elf`和`.bin`格式
5. `烧录执行`: 构建烧录命令并执行,显示烧录进度和结果, 等待烧录完成,观察输出是否成功。烧录后需将 BOOT0 恢复低电平并复位(-s 参数会自动复位,若硬件支持)


## 执行流程
1. 正式烧录前先`握手`: 仅指定-c连接参数（如`STM32_Programmer_CLI -c port=COM3 br=115200`）,不加 -w、-e、-s等操作参数,握手成功即退出,输出芯片型号和容量后返回 0；超时则返回错误
2. 握手成功后再进行正式烧录
3. 烧录成功则返回当前芯片型号和容量,并显示烧录结果；烧录失败则输出错误信息


## 常见问题
1. **无法连接串口**：检查串口号、BOOT0=1、接线(TX↔RX),并确保未占用该串口
2. **烧录失败或校验错误**：确认固件文件正确,尝试增加擦除选项(-e all),检查波特率设置
3. **烧录后无法运行**：提醒用户手动将 BOOT0 接回低电平,按复位键