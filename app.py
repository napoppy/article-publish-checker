import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="多平台文章监测系统", page_icon="📊", layout="wide")

st.title("📊 多平台文章发布状态监测系统")

def detect_platform(url):
    domains = {
        'csdn': ['csdn.net', 'blog.csdn.net'],
        'juejin': ['juejin.cn', 'juejin.im'],
        'freebuf': ['freebuf.com'],
        'zhihu': ['zhihu.com'],
        'xiaohongshu': ['xiaohongshu.com', 'xhslink.com'],
        '51cto': ['51cto.com'],
        'tencent_cloud': ['cloud.tencent.com', 'developer.tencent.com'],
        'aliyun': ['aliyun.com', 'developer.aliyun.com'],
        'jianshu': ['jianshu.com'],
        'cnblogs': ['cnblogs.com'],
        'huawei_cloud': ['huaweicloud.com'],
    }
    url_lower = url.lower()
    for platform, patterns in domains.items():
        for pattern in patterns:
            if pattern in url_lower:
                return platform
    return 'unknown'

def check_url(url, keywords):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, timeout=10, headers=headers)
        status = '可访问' if 200 <= r.status_code < 400 else '不可访问'
        matched = []
        if status == '可访问':
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text().lower()
            for kw in keywords:
                if kw.lower() in text:
                    matched.append(kw)
        return {
            'URL': url,
            '平台': detect_platform(url),
            '发布状态': status,
            '状态码': r.status_code,
            '命中关键词': ', '.join(matched) if matched else '',
            '监测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'URL': url,
            '平台': detect_platform(url),
            '发布状态': '不可访问',
            '状态码': None,
            '命中关键词': '',
            '错误信息': str(e),
            '监测时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

tab1, tab2 = st.tabs(["🔍 URL检测", "📋 历史报告"])

with tab1:
    st.subheader("输入URL进行检测")
    
    url_input = st.text_input("请输入要检测的URL:", placeholder="https://blog.csdn.net/example/article/details/123456")
    
    keywords_input = st.text_input("关键词 (逗号分隔):", value="pandawiki, monkeycode, 开源")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        start_check = st.button("开始检测", type="primary")
    
    if start_check and url_input:
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        with st.spinner("检测中..."):
            result = check_url(url_input, keywords)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("状态", result['发布状态'])
        col2.metric("状态码", result.get('状态码', '-'))
        col3.metric("平台", result['平台'])
        col4.metric("命中关键词", len(result['命中关键词'].split(',')) if result['命中关键词'] else 0)
        
        if result['命中关键词']:
            st.success(f"✅ 命中关键词: {result['命中关键词']}")
        else:
            st.info("未命中关键词")
        
        st.session_state['current_result'] = result

with tab2:
    st.subheader("历史报告")
    csv_files = sorted([f for f in os.listdir('.') if f.startswith('monitor_result_') and f.endswith('.csv')], reverse=True)
    
    if csv_files:
        selected_file = st.selectbox("选择报告:", csv_files)
        df = pd.read_csv(selected_file)
        
        col1, col2, col3, col4 = st.columns(4)
        total = len(df)
        accessible = len(df[df['发布状态'] == '可访问'])
        with_keywords = len(df[df['命中关键词'].notna() & (df['命中关键词'] != '')])
        
        col1.metric("总URL数", total)
        col2.metric("可访问", accessible)
        col3.metric("不可访问", total - accessible)
        col4.metric("命中关键词", with_keywords)
        
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.info("暂无历史报告")
