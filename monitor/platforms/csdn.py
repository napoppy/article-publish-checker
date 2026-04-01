"""
CSDN平台适配器
"""

from typing import Optional
from bs4 import BeautifulSoup

from .base import BasePlatform


class CSDNPlatform(BasePlatform):
    """CSDN博客平台"""

    name = "CSDN"
    domains = ['csdn.net', 'blog.csdn.net']

    def extract_content(self, html: str) -> str:
        """提取CSDN文章正文"""
        soup = BeautifulSoup(html, 'html.parser')
        self.clean_html(soup)

        selectors = [
            '#article_content',
            '.article-content',
            '.blog-content',
            'article',
            '.markdown-body',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text

        main = soup.find('main') or soup.find('article')
        if main:
            return main.get_text(separator=' ', strip=True)

        return soup.get_text(separator=' ', strip=True)[:5000]

    def extract_title(self, html: str) -> Optional[str]:
        """提取CSDN文章标题"""
        soup = BeautifulSoup(html, 'html.parser')

        title_tag = soup.find('h1', class_='article-title') or \
                    soup.find('h1', class_='title-article') or \
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
            '.ad-content', '.advertisement', '.csdn-aside',
            '.recommend-box', '.article-copyright',
            '#ad', '.hide-article-box'
        ]
