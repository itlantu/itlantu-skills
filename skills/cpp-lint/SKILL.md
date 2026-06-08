---
name: cpp-lint
description: "使用clang-format对C++/C代码进行规范检查(仅检查,严禁修改文件)。当用户提到lint、代码规范、代码风格、clang-format、格式检查、静态检查、coding style、格式审查、代码扫描时主动调用。适用于任何包含.cpp/.h/.hpp/.cc/.cxx文件的C/C++项目。对于CMakeLists项目支持从根目录递归扫描所有源文件。即使用户未明确说'用clang-format',只要涉及C++代码格式/规范检查即应使用此技能。"
---

# C++ 代码规范检查

## 工具简介

`clang-format` 是 LLVM 项目的代码格式化工具,支持检查 C/C++ 代码是否符合指定风格规范。

**核心原则：本技能仅进行检查,严禁以任何方式修改源文件。**

## 核心约束

- **绝对禁止修改文件**：必须使用 `--dry-run` / `-n` 参数,绝不允许执行实际格式化
- **严格检查模式**：使用 `clang-format -n` 或 `clang-format --dry-run --Werror`,发现不合规代码时返回非零退出码
- 如需向用户展示差异,使用 `clang-format <file>` 将格式化结果输出到 stdout 进行对比

## 关键参数

| 参数 | 作用 |
|------|------|
| `-n` / `--dry-run` | 检查模式,检查文件是否符合规范,不修改文件 |
| `--Werror` | 将格式警告视为错误,发现违规时返回非零退出码 |
| `--style=<style>` | 指定风格：`file` (默认,读取 `.clang-format`)、`Google`、`LLVM`、`GNU` |
| `--style=file:<path>` | 指定自定义 `.clang-format` 文件路径 |
| `--output-replacements-xml` | 以 XML 格式输出需要修改的位置(可用于统计违规数量) |
| `--verbose` | 输出详细检查过程 |

## 风格配置

### 自动发现(默认)

如果项目根目录存在 `.clang-format` 文件, clang-format 会自动读取使用。检查时优先确认配置文件位置。

### 参考配置

当项目中没有 `.clang-format` 时,从 `references/` 目录选择对应风格的参考文件：

| 风格 | 参考文件 | 适用场景 |
|------|----------|----------|
| Google | `references/google.clang-format` | Google C++ Style Guide 标准 |
| LLVM | `references/llvm.clang-format` | LLVM 项目标准风格 |
| GNU | `references/gnu.clang-format` | GNU 项目标准风格 |

使用方式（路径为技能目录下的相对路径,运行时替换为绝对路径）：
```bash
clang-format --style=file:<项目根目录>/skills/cpp-lint/references/google.clang-format -n <files>
```

## 检查流程

### 1. 确认 clang-format 可用

先检查 `clang-format --version` 是否可正常执行。如果未安装,提示用户安装 LLVM/clang-format。

### 2. 定位配置文件

按优先级查找：
1. 项目根目录的`.clang-format`
2. 上级目录的 `.clang-format` (clang-format 会自动向上查找)
3. 询问用户选择内置参考风格(Google / LLVM / GNU)
4. 用户未指定时默认使用`references/.clang-format`

### 3. 扫描源文件

根据项目类型决定扫描范围：

#### CMakeLists 项目

如果项目根目录存在 `CMakeLists.txt`,以根目录为起点,递归扫描以下扩展名的文件：
- `.cpp` `.cc` `.cxx` `.c++` `.C`
- `.h` `.hpp` `.hh` `.hxx` `.h++`
- `.c` `.m` `.mm` (可选)

**Windows (PowerShell)**：
```powershell
Get-ChildItem -Path . -Recurse -File -Include *.cpp,*.h,*.hpp,*.cc,*.cxx,*.hh,*.c | Where-Object {
    $_.FullName -notmatch '\\build\\|\\cmake-build-|\\third_party\\|\\vendor\\|\\node_modules\\|\\.git\\'
} | ForEach-Object { clang-format -n $_.FullName }
```

**Linux (bash)**：
```bash
find . -type f \( -name "*.cpp" -o -name "*.h" -o -name "*.hpp" -o -name "*.cc" -o -name "*.cxx" -o -name "*.hh" -o -name "*.c" \) \
  ! -path "./build/*" ! -path "./cmake-build-*/*" \
  ! -path "./third_party/*" ! -path "./vendor/*" \
  ! -path "./node_modules/*" ! -path "./.git/*" \
  -print0 | xargs -0 clang-format -n
```

**排除目录**：自动跳过 `build/`、`cmake-build-*/`、`third_party/`、`vendor/`、`node_modules/`、`.git/` 等非项目源码目录。

#### 非 CMakeLists 项目

1. 若有 `.clang-format`, 在 `.clang-format` 所在目录及子目录扫描
2. 无 `.clang-format` 时以当前工作目录为起点扫描
3. 如果用户指定了具体文件/目录,仅检查指定范围

### 4. 执行检查

根据项目平台执行对应的检查命令：

**Windows (PowerShell)**：
```powershell
$files = Get-ChildItem -Recurse -File -Include *.cpp,*.h,*.hpp,*.cc,*.cxx,*.hh | Where-Object {
    $_.FullName -notmatch '\\build\\|\\cmake-build-|\\third_party\\|\\vendor\\|\\node_modules\\|\\.git\\'
}
$errCount = 0
foreach ($f in $files) {
    clang-format -n $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) { $errCount++ }
}
Write-Host "Total files with issues: $errCount"
```

**Linux (bash)**：
```bash
find . -type f \( -name "*.cpp" -o -name "*.h" -o -name "*.hpp" -o -name "*.cc" -o -name "*.cxx" -o -name "*.hh" \) \
  ! -path "./build/*" ! -path "./cmake-build-*/*" \
  ! -path "./third_party/*" ! -path "./vendor/*" \
  ! -path "./node_modules/*" ! -path "./.git/*" \
  -print0 | xargs -0 clang-format -n
```

**单文件检查**：
```bash
clang-format -n <file>
```

**指定风格的单文件检查**：
```bash
clang-format --style=Google -n <file>
```

### 5. 输出报告

检查完成后汇总输出：

- **通过文件数**：格式完全合规的文件
- **违规文件数**：存在格式问题的文件
- **违规详情**：每个违规文件的具体行号和问题描述

输出示例：
```
=== C++ 代码规范检查报告 ===
风格: Google
检查文件数: 42

通过: 38
违规: 4

违规文件列表:
  [FAIL] src/main.cpp:3: 行长度超过80字符,缩进应为空格
  [FAIL] include/foo.h:15: 大括号位置应在同一行
  [FAIL] src/bar.cpp:7: 指针*号应紧跟类型
  [FAIL] test/test_util.cpp:22: 命名空间缩进应为0

=================================
```

## 执行步骤

1. 确认 `clang-format --version` 可用
2. 定位或确认 `.clang-format` 配置, 没有则询问用户是否用默认设置
3. 确定扫描范围(CMakeLists项目从根目录递归扫描,或按用户指定)
4. 执行`clang-format -n`检查所有目标文件
5. 汇总检查结果并输出报告
6. **检查过程中发现违规时,仅报告、不修改。如需修复,告知用户可在原命令中去掉`-n`参数执行格式化**

## 常用命令速查

```bash
# 检查单个文件
clang-format -n src/main.cpp

# 检查多个文件(通配符)
clang-format -n src/*.cpp include/*.h

# 指定风格检查
clang-format --style=LLVM -n src/main.cpp

# 使用指定的 .clang-format 文件
clang-format --style=file:path/to/.clang-format -n src/main.cpp

# 输出需要修改的位置(XML 格式)
clang-format --output-replacements-xml src/main.cpp

# 预览格式化结果(输出到 stdout,不修改文件)
clang-format src/main.cpp
```

## 注意事项

- clang-format 的 `-i` 参数会原地修改文件,**本技能场景中严禁使用**
- `-n` 参数返回码：0 表示格式正确,1 表示需要修改
- 配置文件优先级：`--style` 参数 > `.clang-format` (当前目录) > `.clang-format` (上级目录逐级向上) > 默认配置
- clang-format 自身版本差异可能导致同一配置文件产生不同结果,建议项目锁定 clang-format 版本
