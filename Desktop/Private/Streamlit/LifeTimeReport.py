import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
from datetime import datetime, timedelta
import re

# 日本語フォント設定
rcParams['font.family'] = 'IPAexGothic'
rcParams['axes.unicode_minus'] = False

# カラーマップの定義
shared_cmap = plt.cm.tab10.colors
shared_cmap_large = plt.cm.tab20.colors

# 日時・Duration計算用の関数
def extract_times(date_str):
    pattern = r'(\d{4}/\d{2}/\d{2} \d{1,2}:\d{2}).*?→\s*(?:(\d{4}/\d{2}/\d{2})\s*)?(\d{1,2}:\d{2})'
    if not isinstance(date_str, str):
        return None, None
    m = re.search(pattern, date_str)
    if m:
        start_str = m.group(1)
        end_date_str = m.group(2)
        end_time_str = m.group(3)
        start_dt = datetime.strptime(start_str, '%Y/%m/%d %H:%M')
        end_dt = (
            datetime.strptime(f"{end_date_str} {end_time_str}", '%Y/%m/%d %H:%M')
            if end_date_str else datetime.strptime(f"{start_dt.strftime('%Y/%m/%d')} {end_time_str}", '%Y/%m/%d %H:%M')
        )
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        return start_dt, end_dt
    return None, None

def calc_duration(date_str):
    start_dt, end_dt = extract_times(date_str)
    return (end_dt - start_dt).total_seconds() / 60 if start_dt and end_dt else None

def extract_start_date(date_str):
    start_dt, _ = extract_times(date_str)
    return start_dt

# データアップロード
st.title("LTR Analyzer")
uploaded_file = st.file_uploader("Upload Your LTR(.csv)", type="csv")
<<<<<<< HEAD

# データの読み込み
=======
>>>>>>> 6225b1c (Update LifeTimeReport.py with new functionality)
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # データ処理
    df['Duration (Min)'] = df['Date'].apply(calc_duration)
    df['Start Date'] = df['Date'].apply(extract_start_date)
    df = df.dropna(subset=['Start Date']).copy()
    df['Week Start'] = df['Start Date'].dt.to_period('W').apply(lambda r: r.start_time)

    # 週次集計
    weekly_total = df.groupby('Week Start')['Duration (Min)'].sum().reset_index()
    weekly_total['Recording Ratio (%)'] = (weekly_total['Duration (Min)'] / (7 * 24 * 60)) * 100

    # タグ別集計
    df['Tag List'] = df['Tags'].apply(lambda x: [t.strip() for t in str(x).split(',')] if pd.notnull(x) else [])
    df_tags_week = df[['Week Start', 'Tag List', 'Duration (Min)']].explode('Tag List')
    weekly_tag = df_tags_week.groupby(['Week Start', 'Tag List'], as_index=False)['Duration (Min)'].sum()
    weekly_tag = weekly_tag.rename(columns={'Tag List': 'Tag', 'Duration (Min)': 'Total Duration (Min)'})
    top_tags = weekly_tag.groupby('Tag')['Total Duration (Min)'].sum().nlargest(8).index

    # プロジェクト別集計
    def clean_project_name(name):
        if pd.notnull(name):
            return re.sub(r'\s*\(https?://.*\)$', '', name.strip())
        return name
    df['Project List'] = df['Project'].apply(lambda x: [clean_project_name(p) for p in str(x).split('\n')] if pd.notnull(x) else [])
    df_projects_week = df[['Week Start', 'Project List', 'Duration (Min)']].explode('Project List')
    weekly_project = df_projects_week.groupby(['Week Start', 'Project List'], as_index=False)['Duration (Min)'].sum()
    weekly_project = weekly_project.rename(columns={'Project List': 'Project', 'Duration (Min)': 'Total Duration (Min)'})
    top_projects = weekly_project.groupby('Project')['Total Duration (Min)'].sum().nlargest(8).index

    # (1) 週ごとの全体記録割合の推移
    st.subheader("1. 週ごとの全体記録割合の推移")
    st.write("週次集計データ")
    st.dataframe(weekly_total)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(weekly_total['Week Start'], weekly_total['Recording Ratio (%)'], marker='o', linestyle='-', color=shared_cmap[0])
    ax.set_title("Weekly Record Percentage Trend")
    ax.set_xlabel("Week Start Date")
    ax.set_ylabel("Record Percentage (%)")
    
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # (2) 上位タグの週次推移（積み上げグラフ）
    st.subheader("2. 上位タグの週次推移（積み上げグラフ）")

    top_tags = weekly_tag.groupby('Tag')['Total Duration (Min)'].sum().nlargest(8).index
    top_tags_data = weekly_tag[weekly_tag['Tag'].isin(top_tags)].pivot(index='Week Start', columns='Tag', values='Total Duration (Min)').fillna(0)

    st.write("上位タグ別週次集計データ")
    st.dataframe(top_tags_data)

    # メモリ節約のため間引き
    top_tags_data = top_tags_data.iloc[::2, :]  # データを2行ごとに間引く
    fig, ax = plt.subplots(figsize=(10, 6))
    top_tags_data.plot(kind='bar', stacked=True, ax=ax, color=shared_cmap[:len(top_tags)])
    # x 軸のフォーマットを整形
    formatted_dates = top_tags_data.index.strftime('%Y/%m/%d')  # yyyy/mm/dd形式に変換
    ax.set_xticks(range(len(formatted_dates)))  # インデックスの範囲に設定
    ax.set_xticklabels(formatted_dates, rotation=45, ha="right")  # ラベルを設定
    ax.set_title("Weekly Trend of Major Tags")
    ax.set_xlabel("Week Start Date")
    ax.set_ylabel("Recorded Time (minutes)")

    plt.tight_layout()
    st.pyplot(fig)

    # (3) 上位プロジェクトの週次推移（積み上げグラフ）
    st.subheader("3. 上位プロジェクトの週次推移")
    top_projects = weekly_project.groupby('Project')['Total Duration (Min)'].sum().nlargest(8).index
    top_projects_data = weekly_project[weekly_project['Project'].isin(top_projects)].pivot(index='Week Start', columns='Project', values='Total Duration (Min)').fillna(0)
    
    st.write("上位プロジェクト別週次集計データ")
    st.dataframe(top_projects_data)
    
    # メモリ節約のため間引き
    top_projects_data = top_projects_data.iloc[::2, :]  # データを2行ごとに間引く
    fig, ax = plt.subplots(figsize=(10, 6))
    top_projects_data.plot(kind='bar', stacked=True, ax=ax, color=shared_cmap_large[:len(top_projects)])
    # グラフ枠内のレジェンドを削除
    ax.legend().remove()
    # x 軸のフォーマットを整形
    formatted_dates = top_projects_data.index.strftime('%Y/%m/%d')  # yyyy/mm/dd形式に変換
    ax.set_xticks(range(len(formatted_dates)))  # インデックスの範囲に設定
    ax.set_xticklabels(formatted_dates, rotation=45, ha="right")  # ラベルを設定
    # グラフタイトルとラベル設定
    ax.set_title("Weekly Trend of Major Projects")
    ax.set_xlabel("Week Start Date")
    ax.set_ylabel("Recorded Time (minutes)")
    # レジェンドをグラフ外に配置
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc='upper center', bbox_to_anchor=(0.5, 0.15), ncol=1  # 下部スペースを最小化して配置
    )
    # レイアウト調整
    plt.tight_layout(rect=[0, 0.15, 1, 1])  # 上下余白を調整（rect の値を変更）
    st.pyplot(fig)


    # 任意期間フィルタ
    st.subheader("任意期間のデータ分析")
    start_date = st.date_input("開始日を選択", value=datetime(2024, 1, 1))
    end_date = st.date_input("終了日を選択", value=datetime(2024, 12, 31))
    period_start = pd.Timestamp(start_date)
    period_end = pd.Timestamp(end_date)
    df_period = df[(df['Start Date'] >= period_start) & (df['Start Date'] <= period_end)]

    # (4) タグ別棒グラフ
    st.subheader("4. タグ別棒グラフ")
    df_tags = df_period[['Tag List', 'Duration (Min)']].explode('Tag List')
    tag_duration_sum = df_tags.groupby('Tag List')['Duration (Min)'].sum().reset_index()
    tag_duration_sum_sorted = tag_duration_sum.sort_values('Duration (Min)', ascending=False).head(15)
    total_recorded_duration = tag_duration_sum_sorted['Duration (Min)'].sum()

    st.write("期間内のタグ別集計データ")
    st.dataframe(tag_duration_sum_sorted)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(tag_duration_sum_sorted['Tag List'], tag_duration_sum_sorted['Duration (Min)'], color=shared_cmap[:len(tag_duration_sum_sorted)])
    for bar, duration in zip(bars, tag_duration_sum_sorted['Duration (Min)']):
        percentage = (duration / total_recorded_duration) * 100
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10, f"{duration:.0f}Min\n({percentage:.1f}%)", ha='center', fontsize=9)
    ax.set_title(f"Total Recorded Time by Tag ({start_date}-{end_date})")
    ax.set_xlabel("Tag")
    ax.set_ylabel("Recorded Time (minutes)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # (5) プロジェクト別棒グラフ
    st.subheader("5. プロジェクト別棒グラフ（分数と割合を表示）")
    df_projects = df_period[['Project List', 'Duration (Min)']].explode('Project List')
    project_duration_sum = df_projects.groupby('Project List')['Duration (Min)'].sum().reset_index()
    project_duration_sum_sorted = project_duration_sum.sort_values('Duration (Min)', ascending=False).head(10)
    
    st.write("期間内のプロジェクト別集計データ")
    st.dataframe(project_duration_sum_sorted)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(project_duration_sum_sorted['Project List'], project_duration_sum_sorted['Duration (Min)'], color=shared_cmap_large[:len(project_duration_sum_sorted)])
    for bar, duration in zip(bars, project_duration_sum_sorted['Duration (Min)']):
        percentage = (duration / total_recorded_duration) * 100
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height() / 2, f"{duration:.0f}Min\n({percentage:.1f}%)", va='center', fontsize=9)
    # レジェンドを追加
    handles = [plt.Rectangle((0, 0), 1, 1, color=shared_cmap_large[i]) for i in range(len(project_duration_sum_sorted))]
    labels = project_duration_sum_sorted['Project List'].tolist()
    ax.legend(handles, labels, loc='upper right', title="Project", fontsize=9)
    ax.set_title(f"Total Recorded Time by Project ({start_date}-{end_date})")
    ax.set_xlabel("Recorded Time (minutes)")
    ax.set_yticks([])  # y軸の目盛りとラベルを非表示
    st.pyplot(fig)

# (6) 記録割合円グラフ
    st.subheader("6. 記録割合円グラフ")
    total_period_minutes = max((period_end - period_start).total_seconds() / 60, 0)  # 負の値を防止
    total_recorded_duration = df_period['Duration (Min)'].sum()  # フィルタ済みデータで計算

    st.write("記録割合円グラフに使用されたデータ")
    st.write("総記録時間（分）:", total_recorded_duration)
    st.write("総期間（分）:", total_period_minutes)

    # 微小な誤差に対応
    if abs(total_recorded_duration - total_period_minutes) < 1e-6:
        total_recorded_duration = total_period_minutes

    if total_period_minutes == 0:
        st.warning("選択した期間が無効です。開始日と終了日を確認してください。")
    elif total_recorded_duration > total_period_minutes:
        st.warning("記録された時間が全期間を超えています。データに異常がある可能性があります。")
    else:
        sizes = [total_recorded_duration, total_period_minutes - total_recorded_duration]
        labels = ['Recorded Time', 'Unrecorded Time']
        colors = ['#66b3ff', '#ff9999']

        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            colors=colors, 
            autopct=lambda p: f'{p:.1f}%\n({p * total_period_minutes / 100:.0f}Min)', 
            startangle=90, 
            textprops={'fontsize': 10}
        )
        ax.set_title(f"Percentage of Recorded Time ({start_date}-{end_date})", fontsize=14)
        ax.axis('equal')  # 円を正円に表示
        st.pyplot(fig)
