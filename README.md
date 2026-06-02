# itlantu Skills

---

## Skills

> 使用npx命令可以查看当前可选的skill
```sh
npx skills add itlantu/itlantu-skills --list
```

名称|稳定性|功能|下载
--|--|--|--
stm32-serial-flasher|✅稳定|使用串口烧录STM32 ELF或Bin文件, 需要`STM32_Programmer_CLI`|`npx skill add itlantu/itlantu-skills --path skills/stm32-serial-flash`
usart-serial-communication|✅稳定|提供串口扫描、检测、数据收发与格式转换能力, 基于pyserial|`npx skill add itlantu/itlantu-skills --path skills/usart-serial-communication`
git-commit-message|✅稳定|生成规范化的git commit消息, 遵循`<前缀> <中文描述>`格式|`npx skill add itlantu/itlantu-skills --path skills/git-commit-message`
cpp-lint|⚠️开发中|使用clang-format进行C/C++代码规范检查|`npx skill add itlantu/itlantu-skills --path skills/cpp-lint`

---

## Quick Start

### 1. 确保skill最新

* 首次使用可通过npx skill下载对应的skill

```sh
npx skills add itlantu/itlantu-skills --path skills/<skill-name>
```

* 使用npx skill获取最近的更新
```sh
npx skills add itlantu/lantu-skills --all -y
```

### 2. 在工具中显式调用skill，或隐式触发

* 在工具中调用`/<skill_name> <description>`可显示触发skill
* 示例:
```sh
/stm32-serial-flasher 波特率115200, 烧录build/bin/main.elf到COM3
```
