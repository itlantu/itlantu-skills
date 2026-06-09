---
name: stm32-build
description: "STM32 CMake项目编译与烧录助手。当用户需要编译、构建、烧录固件或进行 STM32 系列芯片的 ST-Link 烧录、调试时使用此技能。关键词包括但不限于：烧录、flash、build、cmake、openocd、ST-Link、STM32、bootloader。"
---

# STM32 CMake 编译 & 烧录

## 工具链

STM32 嵌入式开发推荐使用 STM32CubeCLT 工具链，自带 arm-none-eabi-gcc / CMake / Ninja，无需额外安装。典型安装路径如下（版本号可能不同，以实际安装为准）：

| 工具 | 常见路径 | 用途 |
|---|---|---|
| CMake | `<STM32CubeCLT>/CMake/bin/cmake` | 构建配置 |
| Ninja | `<STM32CubeCLT>/Ninja/bin/ninja` | 构建执行 |
| arm-none-eabi-gcc | `<STM32CubeCLT>/GNU-tools-for-STM32/bin` | 交叉编译器 |
| OpenOCD | `<xpack-openocd>/bin/openocd` | 调试/烧录 |
| OpenOCD scripts | `<xpack-openocd>/openocd/scripts` | 目标/接口配置 |

> 若工具未加入 PATH，需使用绝对路径调用。操作前先确认用户环境中各工具的实际安装路径。

## 编译

### 首次配置与构建

```bash
# 配置 (仅首次或 CMakeLists 变更后)
cmake -B <build_dir> -G Ninja -DCMAKE_BUILD_TYPE=Debug

# 构建
cmake --build <build_dir>
```

常用 `build_dir` 命名约定：
- `cmake-build-debug` — Debug 构建
- `cmake-build-release` — Release 构建

### 新增文件后重新配置

若项目使用 `file(GLOB_RECURSE)` 收集源文件（只在 cmake 配置时扫描），新增 `.c` / `.h` / `.cc` / `.cpp` 后需重新运行配置：

```bash
cmake -B <build_dir> -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build <build_dir>
```

### 修改文件后未重新编译

Ninja 按时间戳判断文件是否变更。若修改后未触发重新编译，手动 `touch` 源文件后构建：

```bash
touch src/xxx.c && cmake --build <build_dir>
```

### 清理重建

```bash
# 完全清理构建目录
rm -rf <build_dir>
cmake -B <build_dir> -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build <build_dir>
```

## 烧录 (ST-Link / OpenOCD)

### 命令格式

```bash
openocd \
  -s <scripts_dir> \
  -f interface/stlink.cfg \
  -f target/<chip_target>.cfg \
  -c "program <elf_path> verify reset exit"
```

### 常用 STM32 target 配置

| 系列 | target 配置文件 | 示例芯片 |
|---|---|---|
| STM32F0 | `target/stm32f0x.cfg` | STM32F030、STM32F051 |
| STM32F1 | `target/stm32f1x.cfg` | STM32F103 |
| STM32F4 | `target/stm32f4x.cfg` | STM32F401、STM32F407、STM32F411 |
| STM32F7 | `target/stm32f7x.cfg` | STM32F767 |
| STM32G0 | `target/stm32g0x.cfg` | STM32G070、STM32G031 |
| STM32L4 | `target/stm32l4x.cfg` | STM32L475、STM32L433 |
| STM32H7 | `target/stm32h7x.cfg` | STM32H743、STM32H750 |

> 在 `<scripts_dir>/target/` 下可查看所有可用配置文件，选择与芯片系列匹配的 target。

### 调试器接口

| 接口 | 配置文件 |
|---|---|
| ST-Link/V2 | `interface/stlink.cfg` |
| ST-Link/V2-1 | `interface/stlink-v2-1.cfg` |
| ST-Link/V3 | `interface/stlink.cfg` |
| J-Link | `interface/jlink.cfg` |
| CMSIS-DAP | `interface/cmsis-dap.cfg` |

### 参数说明

| 参数 | 说明 |
|---|---|
| `-s <scripts_dir>` | OpenOCD 脚本搜索路径 |
| `-f interface/stlink.cfg` | 调试器接口配置 |
| `-f target/<target>.cfg` | 目标芯片系列配置 |
| `program <elf_path>` | 指定要烧录的 ELF 文件 |
| `verify` | 烧录后校验数据完整性 |
| `reset` | 烧录完成后复位芯片 |
| `exit` | 烧录完成后退出 OpenOCD |

### 常用 OpenOCD 命令

```bash
# 仅擦除全部 Flash
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; reset halt; stm32f4x mass_erase 0; exit"

# 解锁 Flash (写保护)
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; reset halt; stm32f4x unlock 0; reset; exit"

# 烧录指定地址的 Bin 文件
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; reset halt; flash write_image erase <bin_path> <start_addr>; reset; exit"
```

## 寄存器调试

### 读取寄存器

```bash
# 运行 N 毫秒后 halt，读取指定寄存器
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/stm32f4x.cfg \
  -c "init; reset; sleep 3000; halt" \
  -c "mdw <addr> <count>" \
  -c "exit"
```

- `mdw` — 按 32 位字读取（Memory Display Word）
- `mdb` — 按 8 位字节读取
- `mdh` — 按 16 位半字读取

### 示例：读取 STM32F4 OTG_FS 寄存器

OTG_FS 基址 `0x50000000`：

| 偏移 | 寄存器 | 说明 |
|---|---|---|
| `0x14` | GINTSTS | 全局中断状态 |
| `0x18` | GINTMSK | 全局中断掩码 |
| `0x20` | GRXSTSP | 接收 FIFO 状态（读即弹出） |
| `0x920` | DIEPCTL1 | EP1 IN 控制 |
| `0xB20` | DOEPCTL1 | EP1 OUT 控制 |
| `0xB2C` | DOEPINT1 | EP1 OUT 中断状态 |

寄存器基址因芯片系列不同而异，具体查阅对应 Reference Manual。

## Bootloader + APP 双分区烧录

典型双分区固件场景：Bootloader 占用前几个 Sector，APP 从 Bootloader 之后开始。

```bash
# 1. 烧录 Bootloader
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/<target>.cfg \
  -c "program <bootloader.elf> verify reset exit"

# 2. 烧录 APP
openocd -s <scripts_dir> -f interface/stlink.cfg -f target/<target>.cfg \
  -c "program <app.elf> verify reset exit"
```

> 确保 Bootloader 和 APP 的 Flash 分区不重叠。首次烧录需先烧 Bootloader 再烧 APP；后续若通过 Bootloader 的 ISP 功能更新 APP，可仅烧录 APP。

## 执行流程

1. `确认工具路径`：询问用户 CMake、Ninja、arm-none-eabi-gcc、OpenOCD 的安装路径。若已加入 PATH 则可直接使用命令名。
2. `确认芯片型号`：向用户确认目标 STM32 芯片型号，以选择正确的 OpenOCD target 配置文件。
3. `确认调试器`：默认使用 ST-Link/V2，若使用 J-Link、CMSIS-DAP 等需更换 `-f interface/` 配置。
4. `确认构建目录与产物`：询问构建目录名和需要烧录的 ELF 文件名，如存在 Bootloader+APP 双分区则分别确认。
5. `编译执行`：先执行 cmake 配置（首次或 CMakeLists 变更后），再执行构建，检查编译输出是否有错误或警告。
6. `烧录执行`：构建 OpenOCD 命令并执行，显示烧录进度和结果，确认校验通过且芯片正常复位。
7. `结果验证`：烧录完成后确认芯片运行正常（可通过串口输出、LED 闪烁等观察）。

## 常见问题

1. **cmake 找不到编译器**：确认 `arm-none-eabi-gcc` 所在目录已加入 PATH，或在 cmake 命令中通过 `-DCMAKE_TOOLCHAIN_FILE=` 指定工具链文件。
2. **编译产物未更新**：若项目使用 `file(GLOB_RECURSE)` 收集源文件，新增文件后需重新运行 `cmake -B <build_dir> -G Ninja` 配置。
3. **OpenOCD 连接失败**：检查 ST-Link USB 连接、目标板供电、调试器驱动是否安装。Windows 下需使用 Zadig 安装 WinUSB 驱动。
4. **烧录失败或校验错误**：确认 ELF 文件路径正确、芯片未被写保护（尝试 `stm32f4x unlock 0`）、Flash 未损坏。
5. **烧录后芯片不运行**：确认烧录的固件入口地址正确，检查 BOOT0 引脚是否为低电平（从 Flash 启动）。
6. **`program` 报地址错误**：ELF 文件中的地址与芯片 Flash 范围不匹配，检查链接脚本中 Flash 起始地址是否正确。
