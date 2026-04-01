"""
平台适配器模块
"""

from .base import BasePlatform
from .csdn import CSDNPlatform
from .juejin import JuejinPlatform

PLATFORM_REGISTRY = {
    'csdn': CSDNPlatform,
    'juejin': JuejinPlatform,
}

def get_platform(name: str):
    """获取平台适配器"""
    return PLATFORM_REGISTRY.get(name, BasePlatform)
