"""
掘金平台适配器
"""

from typing import Optional
from bs4 import BeautifulSoup

from .base import BasePlatform


class JuejinPlatform(BasePlatform):
    """掘金技术社区平台"""

    name = "掘金"
    domains = ['juejin.cn', 'juejin.im']

    def extract_content(self, html: str) -> str:
        """提取掘金文章正文"""
        soup = BeautifulSoup(html, 'html.parser')
        self.clean_html(soup)

        selectors = [
            '.article-content',
            '.markdown-body',
            'article',
            '[class*="content"]',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text

        article = soup.find('article')
        if article:
            return article.get_text(separator=' ', strip=True)

        return soup.get_text(separator=' ', strip=True)[:5000]

    def extract_title(self, html: str) -> Optional[str]:
        """提取掘金文章标题"""
        soup = BeautifulSoup(html, 'html.parser')

        title_tag = soup.find('h1', class_='article-title') or \
                    soup.find('h1', class_='title') or \
                    soup.find('h1')

        if title_tag:
            return title_tag.get_text(strip=True)

        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']

        return None

    def get_exclude_selectors(self) -> list:
        """获取需要排除的元素"""
        return [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            '.author-info', '.sidebar', '.recommended',
            '[class*="author"]', '[class*="sidebar"]'
        ]
