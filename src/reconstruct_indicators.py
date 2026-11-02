# -*- coding: utf-8 -*-
"""
[재구성 예시] 시흥시 지역문화생활 SOC 분석모형 - 지표 산출 로직 재구성

이 스크립트는 원 프로젝트의 납품 코드가 아니다. 실제 분석은 QGIS(버퍼·서비스권역)와
Excel 로 수행되었고, 여기서는 README/docs/methodology.md 에 정리한 지표 정의를
합성 샘플 데이터(data/sample/dong_demand_supply_sample.csv)에 적용해 보이기 위해
다시 구현한 것이다. 수치·가중치는 설명용이며 실제 보고서 값과 무관하다.

입력 컬럼: 행정동, 문화소비금액, 총소비금액, 시설수, 접근성점수, 인구수
출력:
  - data/sample/dong_indicators_result_sample.csv : 수요지수·공급지수·결핍지수·4분면
  - docs/images/lorenz_curve_sample.png            : 시설수 기준 Lorenz 곡선 (지니계수 표시)
실행: python src/reconstruct_indicators.py  (레포 루트에서)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 한글 폰트 설정 (설치된 폰트가 없으면 기본 폰트로 그려지며 한글이 깨질 수 있음)
for _f in ["Malgun Gothic", "AppleGothic", "NanumGothic"]:
    if any(f.name == _f for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = _f
        break
plt.rcParams["axes.unicode_minus"] = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN_CSV = os.path.join(ROOT, "data", "sample", "dong_demand_supply_sample.csv")
OUT_CSV = os.path.join(ROOT, "data", "sample", "dong_indicators_result_sample.csv")
OUT_PNG = os.path.join(ROOT, "docs", "images", "lorenz_curve_sample.png")

W_SUPPLY, W_ACCESS = 0.5, 0.5   # 결핍지수 = 공급량 0.5 + 접근성 0.5 (설명용 가중치)


def minmax(s: pd.Series) -> pd.Series:
    rng = s.max() - s.min()
    return (s - s.min()) / rng if rng > 0 else pd.Series(0.0, index=s.index)


def gini(values) -> float:
    """Lorenz 곡선 아래 면적 기반 지니계수 (0: 완전균등, 1: 완전불균등)."""
    x = np.sort(np.asarray(values, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    cum = np.cumsum(x) / x.sum()
    area = np.trapz(np.concatenate([[0.0], cum]), dx=1.0 / n)   # 곡선 아래 면적
    fair_area = 0.5
    return round((fair_area - area) / fair_area, 4)


def lorenz_points(values):
    x = np.sort(np.asarray(values, dtype=float))
    cum_pop = np.arange(0, len(x) + 1) / len(x)
    cum_val = np.concatenate([[0.0], np.cumsum(x) / x.sum()])
    return cum_pop, cum_val


def main():
    df = pd.read_csv(IN_CSV, encoding="utf-8-sig")

    # 1) 수요지수: 총소비 대비 문화소비 비중을 0-1 로 정규화
    df["문화소비비중"] = df["문화소비금액"] / df["총소비금액"]
    df["수요지수"] = minmax(df["문화소비비중"]).round(3)

    # 2) 공급지수: 인구 1만 명당 시설수(공급량)와 접근성점수를 결합
    df["인구만명당시설수"] = df["시설수"] / df["인구수"] * 10_000
    supply_norm = minmax(df["인구만명당시설수"])
    access_norm = minmax(df["접근성점수"])
    df["공급지수"] = (W_SUPPLY * supply_norm + W_ACCESS * access_norm).round(3)

    # 3) 결핍지수: 공급이 낮을수록 커지도록 1 - 공급지수
    df["결핍지수"] = (1 - df["공급지수"]).round(3)

    # 4) 수요·공급 4분면 (중앙값 기준)
    d_med, s_med = df["수요지수"].median(), df["공급지수"].median()
    def quadrant(r):
        hi_d, hi_s = r["수요지수"] >= d_med, r["공급지수"] >= s_med
        if hi_d and not hi_s:
            return "1_수요高·공급低(우선검토)"
        if hi_d and hi_s:
            return "2_수요高·공급高"
        if not hi_d and not hi_s:
            return "3_수요低·공급低"
        return "4_수요低·공급高"
    df["4분면"] = df.apply(quadrant, axis=1)

    # 5) 지니계수 (시설수, 문화소비금액)
    g_fac, g_cul = gini(df["시설수"]), gini(df["문화소비금액"])
    print(f"지니계수 - 시설수: {g_fac}, 문화소비금액: {g_cul}")
    print(df["4분면"].value_counts().sort_index())

    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    # 6) Lorenz 곡선 저장
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig, ax = plt.subplots(figsize=(5, 5))
    for col, g, c in [("시설수", g_fac, "#2563eb"), ("문화소비금액", g_cul, "#d97706")]:
        px, py = lorenz_points(df[col])
        ax.plot(px, py, color=c, label=f"{col} (Gini={g})")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="완전균등선")
    ax.set_xlabel("행정동 누적 비율"); ax.set_ylabel("값 누적 비율")
    ax.set_title("Lorenz curve (sample data)")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout(); fig.savefig(OUT_PNG, dpi=120); plt.close(fig)
    print("saved:", OUT_CSV, OUT_PNG)


if __name__ == "__main__":
    main()
