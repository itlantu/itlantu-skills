"""检查图片理解技能所需的环境变量是否已配置。"""

import os
import sys

REQUIRED_VARS = [
    "ITLANTU-IMAGE-API-KEY",
    "ITLANTU-IMAGE-BASE-URL",
    "ITLANTU-IMAGE-MODEL",
]


def check_env_vars():
    """检查所有必需的环境变量，报告缺失项。

    返回:
        bool: 全部已配置返回 True，否则返回 False。
    """
    missing = [var for var in REQUIRED_VARS if not os.environ.get(var)]
    if missing:
        print("错误: 以下环境变量未配置：")
        for var in missing:
            print(f"  {var}")
        return False

    print("所有环境变量已配置")
    return True


if __name__ == "__main__":
    if not check_env_vars():
        sys.exit(1)
