# itlantu Skills

---

## 🚀 1. Skills

> 使用npx命令可以查看当前可选的skill
```sh
npx skills add itlantu/itlantu-skills --list
```

名称|稳定性|功能|下载
--|--|--|--
stm32-serial-flasher|✅稳定|使用串口烧录STM32 ELF或Bin文件, 需要`STM32_Programmer_CLI`|`npx skill add itlantu/itlantu-skills --path skills/stm32-serial-flash`
usart-serial-communication|✅稳定|提供串口扫描、检测、数据收发与格式转换能力, 基于pyserial|`npx skill add itlantu/itlantu-skills --path skills/usart-serial-communication`
git-commit-message|✅稳定|生成规范化的git commit消息, 遵循`<前缀> <中文描述>`格式|`npx skill add itlantu/itlantu-skills --path skills/git-commit-message`
c-cpp-coder|✅稳定|C/C++ 代码编写助手，涵盖注释风格、命名规范、代码推荐写法及执行流程|`npx skill add itlantu/itlantu-skills --path skills/c-cpp-coder`
cpp-lint|✅稳定|使用clang-format进行C/C++代码规范检查|`npx skill add itlantu/itlantu-skills --path skills/cpp-lint`
embedded-book|✅稳定|嵌入式硬件模块驱动参考手册，涵盖传感器、执行器、舵机、电机驱动、显示/通信模块的引脚/电源/PWM/协议参数|`npx skill add itlantu/itlantu-skills --path skills/embedded-book`
image-understanding|⚠️开发中|调用多模态大模型获得图像理解能力|`npx skill add itlantu/itlantu-skills --path skills/image-understanding`

---

## ⭐ 2. Quick Start

### 2.1 确保skill最新

* 使用npx skill获取所有itlantu-skills的最近更新
```sh
npx skills add itlantu/lantu-skills --all -y
```

### 2.2 在工具中显式调用skill，或隐式触发

* 在工具中调用`/<skill_name> <description>`可显示触发skill, 示例:
```sh
/stm32-serial-flasher 波特率115200, 烧录build/bin/main.elf到COM3
```

---

## ⚙️ 3. Configuration

### 3.1（可选）image-understanding配置
* 推荐使用`GLM-V`系列模型作为图像理解模型，如`GLM-4.6V-Flash`
* 调用`image-understanding`前需要配置对应的环境变量:

    | Path 环境名 | 作用 |
    |---|---|
    | `ITLANTU-IMAGE-API-KEY` | 图片理解模型的 API Key |
    | `ITLANTU-IMAGE-BASE-URL` | 图片理解模型的 BASE URL |
    | `ITLANTU-IMAGE-MODEL` | 图片理解模型的名称 |