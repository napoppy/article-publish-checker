"""
平台适配器基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from bs4 import BeautifulSoup


class BasePlatform(ABC):
    """平台适配器基类"""

    name: str = "未知平台"
    domains: List[str] = []

    @classmethod
    def match(cls, url: str) -> bool:
        """判断URL是否属于该平台"""
        url_lower = url.lower()
        return any(domain in url_lower for domain in cls.domains)

    @abstractmethod
    def extract_content(self, html: str) -> str:
        """提取正文内容"""
        pass

    @abstractmethod
    def extract_title(self, html: str) -> Optional[str]:
        """提取标题"""
        pass

    def get_exclude_selectors(self) -> List[str]:
        """获取需要排除的选择器"""
        return ['script', 'style', 'nav', 'header', 'footer', 'aside', '.ad', '.advertisement']

    def clean_html(self, soup: BeautifulSoup) -> None:
        """清理HTML中的无关标签"""
        for tag in soup.find_all(self.get_exclude_selectors()):
            tag.decompose()
