# itlantu Skills

---

## Skills

> 使用npx命令可以查看当前可选的skill
```sh
npx skills add itlantu/itlantu-skills --list
```

名称|功能|下载
--|--|--
stm32-serial-flasher|使用串口烧录STM32 ELF或Bin文件, 需要`STM32_Programmer_CLI`|`npx skill add itlantu/itlantu-skills --path skills/stm32-serial-flash`

---

## Quick Start

### 1. 确保skill最新

* 首次使用可通过npx skill下载对应的skill

```sh
npx skills add itlantu/itlantu-skills --path skills/<skill-name>
```

* 使用npx skill获取最近的更新
```sh
npx skills add itlantu/lantu-skills --all -g -y
```

### 2. 在工具中显式调用skill，或隐式触发

* 在工具中调用`/<skill_name> <description>`可显示触发skill
* 示例:
```sh
/stm32-serial-flasher 波特率115200, 烧录build/bin/main.elf到COM3
```
