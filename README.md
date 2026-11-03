# RLSM

<h1 aligin = center><img width="1986" height="1214" alt="image" src="https://github.com/user-attachments/assets/01026822-cc9c-4064-ae61-4ba698597776" /></h1>


RLSM（Rainy Linux Skin Manager）是面向 Linux 的 XXMI Mod 管理器。它读取 XXMI 模块的 `Mods` 目录，在原生 Linux 界面中完成 Mod 导入、分类、启用、停用、预览图设置和删除，并可以读取 Lutris 的游戏启动项与 Wine 环境。

当前版本为 `0.1.0`。绝区零、ZZMI、Lutris、Wine 和 Hyprland 的主要流程已经在 Arch Linux 环境中实际使用。其他 XXMI 模块已经加入路径、进程和启动项定义，仍需在对应游戏环境中继续验证。

## 当前功能

- 在 `~/Games` 中查找 XXMI Launcher 和已经安装的模块，也可以手动选择模块目录。
- 检查模块的 `Mods` 目录、`d3dx.ini`、递归载入设置和 `DISABLED*` 排除设置。
- 递归读取 Mod，显示名称、启用状态和预览图。
- 通过重命名 Mod 目录完成启用与停用。
- 支持同一分类内只启用一个 Mod。
- 导入文件夹、ZIP、7z 和 RAR，导入后的 Mod 默认保持停用。
- 根据 Mod 元数据、模型文件名称和目录名称尝试整理分类。
- 为每个 Mod 设置 PNG、JPEG、WebP、BMP 或 GIF 预览图。
- 将删除的 Mod 移入系统回收站。
- 读取 Lutris 数据库和游戏配置，识别游戏启动项、Wine 运行器与 Wine 前缀。
- 从 RLSM 启动已经绑定的 Lutris 游戏。
- 在 Hyprland 中向游戏窗口发送 `F10`，也可以在切换 Mod 后自动发送。
- 自定义窗口背景、背景遮罩、图片显示方式和主题颜色。

## XXMI 模块

RLSM 当前包含以下模块定义：

- ZZMI：绝区零，主要流程已经实际使用。
- EFMI：明日方舟：终末地。
- WWMI：鸣潮。
- GIMI：原神。
- SRMI：崩坏：星穹铁道。
- HIMI：崩坏3。

除 ZZMI 外，其余模块目前表示 RLSM 已经能够识别相应的 XXMI 目录、游戏进程和 Lutris 启动项。具体的 Mod 切换和游戏内刷新效果仍需在对应游戏中验证。

## 运行条件

- Linux 桌面环境。
- Python 3.12 或更高版本。
- 已经安装并配置对应的 XXMI 模块。
- Mod 模块目录中存在 `d3dx.ini` 和 `Mods` 目录。

以下组件按功能选用：

- Lutris：读取游戏启动项、Wine 运行器和 Wine 前缀，并启动游戏。
- Hyprland 与 `hyprctl`：向游戏窗口发送 `F10`。
- `gio`：把 Mod 移入系统回收站，通常由 GLib 提供。
- `bsdtar`：导入 7z 和 RAR 压缩包，通常由 libarchive 提供。ZIP 导入使用 Python 自带功能。

Python 依赖由项目配置安装：

- PySide6：Qt 界面。
- PyYAML：读取 Lutris 配置。

## 从源码启动

```bash
git clone git@github.com:OctoberPrayRain/RLSM-XXMI.git
cd RLSM-XXMI
python -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m rlsm
```

开发时也可以直接从源码目录启动：

```bash
PYTHONPATH=src .venv/bin/python -m rlsm
```

## 基本使用

1. 在顶部选择游戏和 XXMI 模块。
2. 如果 RLSM 没有自动找到模块，在“游戏环境”中选择对应的模块目录，例如 `ZZMI` 或 `EFMI`。
3. 检查环境信息。RLSM 会提示 `Mods` 目录、`d3dx.ini` 或递归载入设置中的问题。
4. 在“Lutris 与 Wine”中选择游戏启动项。需要时可以单独指定 Wine 前缀。
5. 回到“Mod 资料库”，导入 Mod 文件夹或压缩包。
6. 使用卡片上的“启用”“停用”“预览图”和“删除”管理 Mod。
7. 游戏正在运行时，可以发送 `F10`，或者开启切换 Mod 后自动发送 `F10`。

## Mod 目录规则

RLSM 使用 XXMI 已有的目录规则管理状态：

- 启用状态保留原目录名称。
- 停用状态在目录名称前添加 `DISABLED_`。
- “分类内单选”会停用同一分类中已经启用的其他 Mod。
- 导入同名 Mod 时会建立新的目录，不会覆盖现有 Mod。
- 自动分类只整理 `Mods` 根目录和“未分类”目录中的内容。

RLSM 导入 Mod 时会在 Mod 目录中保存 `.rlsm.json`。手动设置的预览图会保存为 `.rlsm-preview` 加原图片扩展名。更换预览图时，RLSM 会删除先前由自身保存的预览图。

## Lutris 与 Wine

RLSM 从 Lutris 的本地数据库和 YAML 配置中读取：

- 游戏名称、标识和启动地址。
- 游戏可执行文件与工作目录。
- Wine 前缀、Wine 运行器和架构。
- Lutris 为启动项设置的环境变量。
- 启动参数中的 `--xxmi` 模块提示。

RLSM 使用 Lutris 自身的启动地址打开游戏。Wine 前缀用于确认 Mod 管理器连接的是对应的游戏环境。

## Hyprland 刷新

启用自动刷新后，RLSM 会在 Mod 状态发生变化时查找对应的游戏窗口，并向该窗口发送 `F10`。窗口匹配会检查窗口类名、标题、进程名称和可执行文件路径。

该功能需要在 Hyprland 会话中运行，并且系统能够执行 `hyprctl`。其他桌面环境仍可使用 Mod 管理、Lutris 和 Wine 功能。

## 项目结构

- `src/rlsm/application`：Mod 扫描、导入、分类、状态切换、预览图和删除操作。
- `src/rlsm/domain`：游戏、Mod、Wine 环境和启动项的数据定义。
- `src/rlsm/infrastructure`：XXMI、Lutris 和 Hyprland 的读取与控制。
- `src/rlsm/presentation`：界面状态、设置和操作入口。
- `src/rlsm/qml`：Qt Quick 界面、主题和组件。
- `pyproject.toml`：Python 包与依赖配置。
- `pysidedeploy.spec`、`RLSM.pyproject`：独立程序打包配置。

## 开发状态

当前阶段重点是完善 Linux 下的 XXMI Mod 管理流程。项目已经保留独立程序打包配置，界面调整期间建议从源码启动，便于直接检查修改结果。

已知范围：

- 自动分类依赖 Mod 元数据、文件名称和目录名称，无法识别的内容会保留在“未分类”。
- 7z 和 RAR 导入依赖系统中的 `bsdtar`。
- 游戏内自动刷新目前使用 Hyprland 窗口控制。
- EFMI、WWMI、GIMI、SRMI 和 HIMI 仍需要对应游戏环境的实际验证。

## 许可证

RLSM 使用 [MIT License](LICENSE)。
