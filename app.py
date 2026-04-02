import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="多平台文章监测系统", page_icon="📊", layout="wide")

st.title("📊 多平台文章发布状态监测系统")

def load_results():
    csv_files = [f for f in os.listdir('.') if f.startswith('monitor_result_') and f.endswith('.csv')]
    if csv_files:
        latest = sorted(csv_files)[-1]
        return pd.read_csv(latest), latest
    return None, None

df, filename = load_results()

if df is not None:
    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    accessible = len(df[df['发布状态'] == '可访问'])
    inaccessible = total - accessible
    with_keywords = len(df[df['命中关键词'].notna() & (df['命中关键词'] != '')])
    
    col1.metric("总URL数", total)
    col2.metric("可访问", accessible, f"{accessible/total*100:.1f}%")
    col3.metric("不可访问", inaccessible, f"{inaccessible/total*100:.1f}%")
    col4.metric("命中关键词", with_keywords)
    
    st.divider()
    st.subheader(f"📋 监测报告: {filename}")
    
    platform_filter = st.multiselect(
        "筛选平台",
        options=df['平台'].unique(),
        default=df['平台'].unique()
    )
    
    filtered = df[df['平台'].isin(platform_filter)]
    
    def color_status(val):
        return 'color: green' if val == '可访问' else 'color: red'
    
    st.dataframe(
        filtered.style.applymap(color_status, subset=['发布状态']),
        use_container_width=True,
        height=500
    )
    
    st.divider()
    st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.info("📂 暂无监测报告，请先运行 `python main.py` 生成报告")
    st.code("python main.py -m 10", language="bash")
