#!/usr/bin/env python3
"""
多平台文章发布状态+关键词监测系统
功能：校验URL发布状态、检测关键词、生成监测报告
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import yaml
import pandas as pd
from urllib.parse import urlparse

try:
    import asyncio
    import aiohttp
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    asyncio = None
    aiohttp = None


VERSION = "1.0.0"
DEFAULT_TIMEOUT = 10
MAX_RETRIES = 2
REQUEST_INTERVAL = 1.0


class ConfigLoader:
    """配置加载模块：读取config.yaml，解析关键词、平台规则、请求参数"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = {}
        self.keywords = []
        self.platform_rules = {}
        self.request_params = {}
        self.load()

    def load(self) -> None:
        """加载并解析配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self.keywords = self.config.get('keywords', [])
        self.platform_rules = self.config.get('platform_rules', {})
        self.request_params = self.config.get('request_params', {})

        logging.info(f"配置加载成功: {len(self.keywords)}个关键词, {len(self.platform_rules)}个平台规则")

    def get_headers(self) -> Dict[str, str]:
        """获取请求头配置"""
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        if 'headers' in self.request_params:
            default_headers.update(self.request_params['headers'])
        return default_headers

    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.request_params.get('timeout', DEFAULT_TIMEOUT)

    def get_retry_times(self) -> int:
        """获取重试次数"""
        return self.request_params.get('retry_times', MAX_RETRIES)

    def get_request_interval(self) -> float:
        """获取请求间隔"""
        return self.request_params.get('interval', REQUEST_INTERVAL)


class URLValidator:
    """URL有效性校验模块：发送HTTP请求，校验状态码，处理超时/重试"""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.get_headers())

    def validate_url(self, url: str, retry_times: Optional[int] = None) -> Dict[str, Any]:
        """
        校验URL有效性
        返回: {
            'url': str,
            'accessible': bool,
            'status_code': int or None,
            'error': str or None
        }
        """
        if retry_times is None:
            retry_times = self.config.get_retry_times()

        for attempt in range(retry_times + 1):
            try:
                start_time = time.time()
                response = self.session.get(
                    url,
                    timeout=self.config.get_timeout(),
                    allow_redirects=True
                )
                elapsed = time.time() - start_time

                result = {
                    'url': url,
                    'accessible': 200 <= response.status_code < 400,
                    'status_code': response.status_code,
                    'elapsed': round(elapsed, 3),
                    'error': None
                }

                if result['accessible']:
                    return result
                elif attempt < retry_times:
                    logging.warning(f"URL {url} 返回状态码 {response.status_code}，第{attempt + 1}次重试...")
                    time.sleep(1)
                    continue
                else:
                    result['error'] = f"HTTP {response.status_code}"
                    return result

            except requests.exceptions.Timeout:
                if attempt < retry_times:
                    logging.warning(f"URL {url} 超时，第{attempt + 1}次重试...")
                    time.sleep(1)
                    continue
                else:
                    return {
                        'url': url,
                        'accessible': False,
                        'status_code': None,
                        'elapsed': None,
                        'error': 'Timeout'
                    }
            except requests.exceptions.RequestException as e:
                if attempt < retry_times:
                    logging.warning(f"URL {url} 请求异常: {e}，第{attempt + 1}次重试...")
                    time.sleep(1)
                    continue
                else:
                    return {
                        'url': url,
                        'accessible': False,
                        'status_code': None,
                        'elapsed': None,
                        'error': str(e)
                    }

        return {
            'url': url,
            'accessible': False,
            'status_code': None,
            'elapsed': None,
            'error': 'Max retries exceeded'
        }


class PlatformDetector:
    """平台检测器：根据URL识别目标平台"""

    PLATFORM_PATTERNS = {
        'csdn': ['csdn.net', 'blog.csdn.net'],
        'juejin': ['juejin.cn', 'juejin.im'],
        'freebuf': ['freebuf.com'],
        'zhihu': ['zhihu.com'],
        'xiaohongshu': ['xiaohongshu.com', 'xhslink.com'],
        '51cto': ['51cto.com', 'blog.51cto.com'],
        'tencent_cloud': ['cloud.tencent.com', 'developer.tencent.com'],
        'aliyun': ['aliyun.com', 'developer.aliyun.com'],
        'jianshu': ['jianshu.com'],
        'cnblogs': ['cnblogs.com', 'www.cnblogs.com'],
        'huawei_cloud': ['huaweicloud.com', 'developer.huaweicloud.com'],
        'bilibili': ['bilibili.com'],
        '360doc': ['360doc.com'],
        'smzdm': ['smzdm.com'],
        'douban': ['douban.com'],
        'toutiao': ['toutiao.com', '星图' ],
        'volcengine': ['volcengine.com', '火山引擎'],
        'jike': ['jike.im', '即刻'],
        'kaiwu': ['kaiwu.lagou', '拉勾'],
        'oschina': ['oschina.net', '开源中国'],
        'geektime': ['geektime.com', '极客时间'],
    }

    @classmethod
    def detect(cls, url: str) -> str:
        """根据URL检测平台类型"""
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')

        for platform, patterns in cls.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if pattern in domain:
                    return platform

        return 'unknown'


class ContentExtractor:
    """正文提取+关键词检测模块：按平台规则提取正文，匹配关键词"""

    def __init__(self, config: ConfigLoader):
        self.config = config
        self.keywords = [kw.lower() for kw in config.keywords]

    def extract_and_check(self, url: str, html: str, platform: str) -> Dict[str, Any]:
        """
        提取正文并检测关键词
        返回: {
            'platform': str,
            'content': str,
            'matched_keywords': List[str],
            'has_keywords': bool
        }
        """
        content = self._extract_content(html, platform)
        matched = self._check_keywords(content)

        return {
            'platform': platform,
            'content': content,
            'matched_keywords': matched,
            'has_keywords': len(matched) > 0
        }

    def _extract_content(self, html: str, platform: str) -> str:
        """根据平台提取正文内容"""
        soup = BeautifulSoup(html, 'html.parser')

        selectors = {
            'csdn': ['article', '.article-content', '#article_content', '.blog-content'],
            'juejin': ['article', '.article-content', '.markdown-body', '[class*="content"]'],
            'freebuf': ['article', '.article-content', '.post-content'],
            'zhihu': ['article', '.RichText', '[class*="Article"]'],
            'xiaohongshu': ['article', '.note-content', '[class*="content"]'],
            '51cto': ['article', '.article-content', '.content-detail'],
            'tencent_cloud': ['article', '.article-content', '.markdown-content'],
            'aliyun': ['article', '.article-content', '.markdown-body'],
            'jianshu': ['article', '.note-content', '.show-content'],
            'cnblogs': ['article', '.blogpost-body', '.post-body'],
            'huawei_cloud': ['article', '.article-content', '.markdown-body'],
            'bilibili': ['article', '.article-content', '.bb-comment'],
            '360doc': ['article', '.article-text', '.content'],
            'smzdm': ['article', '.article-wrap', '.content-detail'],
            'douban': ['article', '.topic-content', '.rich-content'],
            'toutiao': ['article', '.article-content', '.article-body'],
            'volcengine': ['article', '.article-content', '.markdown-body'],
            'jike': ['article', '.note-content', '.markdown-body'],
            'oschina': ['article', '.article-content', '.markdown-body'],
            'geektime': ['article', '.article-content', '.markdown-body'],
        }

        platform_selectors = selectors.get(platform, ['article', 'main', '[class*="content"]'])

        for selector in platform_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return text

        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()

        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: bool(x and 'content' in str(x).lower()))
        if main_content:
            return main_content.get_text(separator=' ', strip=True)

        return soup.get_text(separator=' ', strip=True)[:5000]

    def _check_keywords(self, content: str) -> List[str]:
        """检测内容中是否包含关键词（不区分大小写）"""
        if not content:
            return []

        content_lower = content.lower()
        matched = []

        for keyword in self.keywords:
            if keyword.lower() in content_lower:
                matched.append(keyword)

        return list(set(matched))


class ResultAggregator:
    """结果汇总模块：统计监测结果，生成控制台输出和CSV文件"""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def add_result(self, result: Dict[str, Any]) -> None:
        """添加单条监测结果"""
        self.results.append(result)

    def add_results(self, results: List[Dict[str, Any]]) -> None:
        """批量添加监测结果"""
        self.results.extend(results)

    def generate_csv(self) -> str:
        """生成CSV报告文件"""
        today = datetime.now().strftime('%Y%m%d')
        csv_path = self.output_dir / f"monitor_result_{today}.csv"

        df = pd.DataFrame([{
            'URL': r.get('url', ''),
            '平台': r.get('platform', ''),
            '发布状态': '可访问' if r.get('accessible') else '不可访问',
            '状态码': r.get('status_code', ''),
            '命中关键词': ', '.join(r.get('matched_keywords', [])) if r.get('matched_keywords') else '',
            '错误信息': r.get('error', ''),
            '监测时间': r.get('check_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        } for r in self.results])

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logging.info(f"CSV报告已生成: {csv_path}")
        return str(csv_path)

    def print_console_output(self) -> None:
        """控制台按平台分组展示结构化结果"""
        if not self.results:
            print("\n没有监测结果可展示")
            return

        platform_groups = {}
        for r in self.results:
            platform = r.get('platform', 'unknown')
            if platform not in platform_groups:
                platform_groups[platform] = []
            platform_groups[platform].append(r)

        print("\n" + "=" * 80)
        print("多平台文章发布状态监测报告".center(60))
        print("=" * 80)

        total_accessible = sum(1 for r in self.results if r.get('accessible'))
        total_with_keywords = sum(1 for r in self.results if r.get('has_keywords'))
        total_urls = len(self.results)

        print(f"\n【汇总统计】总URL数: {total_urls} | 可访问: {total_accessible} | 命中关键词: {total_with_keywords}\n")

        for platform, items in sorted(platform_groups.items()):
            print(f"\n{'─' * 40}")
            print(f"【{self._get_platform_name(platform)}】({len(items)}个URL)")
            print(f"{'─' * 40}")

            header = f"{'URL':<45} {'状态':<8} {'关键词':<20}"
            print(header)
            print("-" * 75)

            for r in items[:10]:
                url = r.get('url', '')[:42] + '...' if len(r.get('url', '')) > 45 else r.get('url', '')
                status = '✓ 可访问' if r.get('accessible') else '✗ 不可访问'
                keywords = ', '.join(r.get('matched_keywords', [])[:3])
                if len(r.get('matched_keywords', [])) > 3:
                    keywords += '...'
                keywords = keywords[:18] + '..' if len(keywords) > 20 else keywords

                print(f"{url:<45} {status:<8} {keywords:<20}")

            if len(items) > 10:
                print(f"... 还有 {len(items) - 10} 个URL")

        print("\n" + "=" * 80)

    def _get_platform_name(self, platform: str) -> str:
        """获取平台中文名称"""
        names = {
            'csdn': 'CSDN',
            'juejin': '掘金',
            'freebuf': 'FreeBuf',
            'zhihu': '知乎',
            'xiaohongshu': '小红书',
            '51cto': '51CTO',
            'tencent_cloud': '腾讯云开发者',
            'aliyun': '阿里云开发者',
            'jianshu': '简书',
            'cnblogs': '博客园',
            'huawei_cloud': '华为云博客',
            'bilibili': 'B站动态',
            '360doc': '360doc',
            'smzdm': '什么值得买',
            'douban': '豆瓣',
            'toutiao': '今日头条',
            'volcengine': '火山引擎开发者',
            'jike': '即刻',
            'oschina': '开源中国',
            'geektime': '极客时间',
            'unknown': '未知平台'
        }
        return names.get(platform, platform)

    def get_summary(self) -> Dict[str, Any]:
        """获取汇总统计"""
        return {
            'total': len(self.results),
            'accessible': sum(1 for r in self.results if r.get('accessible')),
            'inaccessible': sum(1 for r in self.results if not r.get('accessible')),
            'with_keywords': sum(1 for r in self.results if r.get('has_keywords')),
            'without_keywords': sum(1 for r in self.results if r.get('accessible') and not r.get('has_keywords')),
        }


class ArticleMonitor:
    """文章监测系统主类"""

    def __init__(self, config_path: str = "config.yaml", urls_file: str = "urls.txt"):
        self.config_loader = ConfigLoader(config_path)
        self.url_validator = URLValidator(self.config_loader)
        self.content_extractor = ContentExtractor(self.config_loader)
        self.result_aggregator = ResultAggregator()
        self.urls_file = urls_file
        self.urls = []

    def load_urls(self) -> List[str]:
        """从文件加载URL列表"""
        if not os.path.exists(self.urls_file):
            logging.error(f"URL列表文件不存在: {self.urls_file}")
            return []

        with open(self.urls_file, 'r', encoding='utf-8') as f:
            self.urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        logging.info(f"成功加载 {len(self.urls)} 个URL")
        return self.urls

    def monitor_url(self, url: str) -> Dict[str, Any]:
        """监测单个URL"""
        result = {
            'url': url,
            'platform': PlatformDetector.detect(url),
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        validation = self.url_validator.validate_url(url)
        result.update(validation)

        if validation['accessible']:
            try:
                response = self.url_validator.session.get(url, timeout=self.config_loader.get_timeout())
                content_result = self.content_extractor.extract_and_check(
                    url, response.text, result['platform']
                )
                result.update(content_result)
            except Exception as e:
                logging.error(f"提取内容失败 {url}: {e}")
                result['error'] = f"Content extraction failed: {e}"
        else:
            result['matched_keywords'] = []
            result['has_keywords'] = False

        return result

    def run_sync(self, max_urls: Optional[int] = None) -> None:
        """同步模式运行监测"""
        urls = self.load_urls()
        if max_urls:
            urls = urls[:max_urls]

        if not urls:
            logging.warning("没有需要监测的URL")
            return

        print(f"\n开始监测 {len(urls)} 个URL...")
        print(f"请求间隔: {self.config_loader.get_request_interval()}秒")

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] 监测: {url[:60]}...")
            result = self.monitor_url(url)
            self.result_aggregator.add_result(result)

            if i < len(urls):
                time.sleep(self.config_loader.get_request_interval())

        self.result_aggregator.print_console_output()
        csv_path = self.result_aggregator.generate_csv()
        summary = self.result_aggregator.get_summary()

        print(f"\n监测完成! CSV报告: {csv_path}")
        print(f"汇总: 总计{summary['total']}个, 可访问{summary['accessible']}个, "
              f"命中关键词{summary['with_keywords']}个")

    def run_async(self, max_urls: Optional[int] = None, concurrency: int = 5) -> None:
        """异步模式运行监测（需要aiohttp）"""
        if not ASYNC_AVAILABLE:
            logging.warning("aiohttp未安装，将使用同步模式")
            self.run_sync(max_urls)
            return

        urls = self.load_urls()
        if max_urls:
            urls = urls[:max_urls]

        if not urls:
            logging.warning("没有需要监测的URL")
            return

        print(f"\n开始异步监测 {len(urls)} 个URL... (并发数: {concurrency})")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._async_monitor(urls, concurrency))

        self.result_aggregator.print_console_output()
        csv_path = self.result_aggregator.generate_csv()
        summary = self.result_aggregator.get_summary()

        print(f"\n监测完成! CSV报告: {csv_path}")
        print(f"汇总: 总计{summary['total']}个, 可访问{summary['accessible']}个, "
              f"命中关键词{summary['with_keywords']}个")

    async def _async_monitor(self, urls: List[str], concurrency: int) -> None:
        """异步监测核心逻辑"""
        semaphore = asyncio.Semaphore(concurrency)
        session = aiohttp.ClientSession(headers=self.config_loader.get_headers())

        async def monitor_one(url: str) -> Dict[str, Any]:
            async with semaphore:
                result = {
                    'url': url,
                    'platform': PlatformDetector.detect(url),
                    'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                for attempt in range(self.config_loader.get_retry_times() + 1):
                    try:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.config_loader.get_timeout())) as response:
                            result['status_code'] = response.status
                            result['accessible'] = 200 <= response.status < 400
                            result['elapsed'] = response.total_time if hasattr(response, 'total_time') else None

                            if result['accessible']:
                                html = await response.text()
                                content_result = self.content_extractor.extract_and_check(url, html, result['platform'])
                                result.update(content_result)
                            else:
                                result['error'] = f"HTTP {response.status}"
                                result['matched_keywords'] = []
                                result['has_keywords'] = False
                            break

                    except asyncio.TimeoutError:
                        if attempt < self.config_loader.get_retry_times():
                            await asyncio.sleep(1)
                            continue
                        result.update({
                            'accessible': False,
                            'status_code': None,
                            'error': 'Timeout',
                            'matched_keywords': [],
                            'has_keywords': False
                        })
                    except Exception as e:
                        if attempt < self.config_loader.get_retry_times():
                            await asyncio.sleep(1)
                            continue
                        result.update({
                            'accessible': False,
                            'status_code': None,
                            'error': str(e),
                            'matched_keywords': [],
                            'has_keywords': False
                        })

                return result

        tasks = [monitor_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, dict):
                self.result_aggregator.add_result(result)
            else:
                logging.error(f"监测异常: {result}")

        await session.close()


def setup_logging(log_file: Optional[str] = None) -> None:
    """配置日志记录"""
    today = datetime.now().strftime('%Y%m%d')

    if log_file is None:
        log_file = f"monitor_log_{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """主入口函数"""
    import argparse

    parser = argparse.ArgumentParser(description='多平台文章发布状态+关键词监测系统')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('-u', '--urls', default='urls.txt', help='URL列表文件路径')
    parser.add_argument('-m', '--max', type=int, default=None, help='最大监测URL数量')
    parser.add_argument('-a', '--async', dest='use_async', action='store_true', help='使用异步模式')
    parser.add_argument('-p', '--parallel', type=int, default=5, help='异步并发数')
    parser.add_argument('-o', '--output', default='.', help='输出目录')
    parser.add_argument('-l', '--log', default=None, help='日志文件路径')

    args = parser.parse_args()

    setup_logging(args.log)

    logging.info(f"=== 多平台文章监测系统启动 (v{VERSION}) ===")

    try:
        monitor = ArticleMonitor(args.config, args.urls)
        monitor.result_aggregator = ResultAggregator(args.output)

        if args.use_async and ASYNC_AVAILABLE:
            monitor.run_async(max_urls=args.max, concurrency=args.parallel)
        else:
            monitor.run_sync(max_urls=args.max)

    except FileNotFoundError as e:
        logging.error(f"文件不存在: {e}")
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"系统异常: {e}", exc_info=True)
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
