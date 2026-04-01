# 多平台文章发布状态+关键词监测系统

用于批量监测多平台文章发布状态和关键词检测的工具。

## 功能特性

- URL有效性校验（状态码、超时重试）
- 正文内容提取
- 关键词检测（不区分大小写）
- 平台自动识别
- 支持同步/异步请求模式
- 控制台表格输出
- CSV报告生成
- 日志记录

## 支持平台

CSDN、掘金、FreeBuf、知乎、小红书、51CTO、腾讯云开发者、阿里云开发者、简书、博客园、华为云博客、B站动态、360doc、什么值得买、豆瓣、今日头条、火山引擎开发者、即刻、开源中国、极客时间等

## 项目结构

```
article-monitor/
├── main.py              # 主程序入口
├── config.yaml          # 配置文件
├── urls.txt             # URL列表文件
├── requirements.txt     # Python依赖
├── README.md            # 说明文档
└── monitor/
    ├── __init__.py
    └── platforms/       # 平台适配器
        ├── __init__.py
        ├── base.py
        ├── csdn.py
        └── juejin.py
```

## 依赖安装

```bash
pip install -r requirements.txt
```

或使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置说明

### config.yaml

```yaml
keywords:
  - monkeycode
  - pandawiki
  - 开源
  - 极客

request_params:
  timeout: 10
  retry_times: 2
  interval: 1.0
```

### urls.txt

每行一个URL，支持以 `#` 开头的注释：

```
# CSDN文章
https://blog.csdn.net/example/article/details/123456

# 掘金文章
https://juejin.cn/post/123456789
```

## 运行方式

### 基本用法（同步模式）

```bash
python main.py
```

### 异步模式（推荐用于大量URL）

```bash
python main.py -a
```

### 指定参数

```bash
# 指定配置文件和URL列表
python main.py -c config.yaml -u urls.txt

# 限制最大监测URL数量
python main.py -m 10

# 指定异步并发数
python main.py -a -p 10

# 指定输出目录
python main.py -o ./output
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| -c, --config | 配置文件路径 | config.yaml |
| -u, --urls | URL列表文件路径 | urls.txt |
| -m, --max | 最大监测URL数量 | 全部 |
| -a, --async | 使用异步模式 | False |
| -p, --parallel | 异步并发数 | 5 |
| -o, --output | 输出目录 | 当前目录 |
| -l, --log | 日志文件路径 | 自动生成 |

## 输出说明

### 控制台输出

按平台分组展示监测结果：

```
================================================================================
                    多平台文章发布状态监测报告
================================================================================

【汇总统计】总URL数: 20 | 可访问: 18 | 命中关键词: 5

----------------------------------------
【CSDN】(5个URL)
----------------------------------------
URL                                             状态     关键词
---------------------------------------------------------------------------
https://blog.csdn.net/...                       ✓ 可访问   monkeycode
...

----------------------------------------
【掘金】(3个URL)
----------------------------------------
...
```

### CSV报告

文件：`monitor_result_YYYYMMDD.csv`

| 字段 | 说明 |
|------|------|
| URL | 文章链接 |
| 平台 | 平台名称 |
| 发布状态 | 可访问/不可访问 |
| 状态码 | HTTP状态码 |
| 命中关键词 | 匹配的关键词列表 |
| 错误信息 | 错误描述 |
| 监测时间 | 监测时间戳 |

### 日志文件

文件：`monitor_log_YYYYMMDD.log`

记录监测过程中的所有异常和关键信息。

## 扩展指南

### 新增关键词

编辑 `config.yaml`，在 `keywords` 列表中添加：

```yaml
keywords:
  - monkeycode
  - pandawiki
  - 新关键词
```

### 新增平台适配器

1. 在 `monitor/platforms/` 目录下创建新文件，如 `zhihu.py`：

```python
from bs4 import BeautifulSoup
from .base import BasePlatform

class ZhihuPlatform(BasePlatform):
    name = "知乎"
    domains = ['zhihu.com']

    def extract_content(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        # 实现提取逻辑
        ...

    def extract_title(self, html: str) -> str:
        # 实现标题提取
        ...
```

2. 在 `monitor/platforms/__init__.py` 中注册：

```python
from .zhihu import ZhihuPlatform

PLATFORM_REGISTRY = {
    'csdn': CSDNPlatform,
    'juejin': JuejinPlatform,
    'zhihu': ZhihuPlatform,  # 新增
}
```

3. 在 `main.py` 的 `PlatformDetector.PLATFORM_PATTERNS` 中添加域名匹配规则。

## 注意事项

1. 请求频率限制：默认1秒/次，避免对目标网站造成压力
2. 超时重试：默认重试2次
3. 小红书等JS渲染页面建议使用异步模式以获得更好的稳定性
4. 如需处理更复杂的JS渲染页面，可集成 `playwright` 或 `selenium`

## 许可证

MIT License
