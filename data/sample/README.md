# 샘플 데이터 안내

- `dong_demand_supply_sample.csv` — 행정동 20개, numpy seed 42 난수로 만든 **합성 데이터**. `src/reconstruct_indicators.py`의 입력.
  - `행정동`, `문화소비금액`, `총소비금액`(원), `시설수`, `접근성점수`(0–1, QGIS 750m 버퍼 접근성을 대신하는 자리), `인구수`
- `dong_indicators_result_sample.csv` — 위 스크립트의 출력. `문화소비비중, 수요지수, 인구만명당시설수, 공급지수, 결핍지수, 4분면` 컬럼이 추가된다.
- 실제 시흥시 행정동 값과 무관하며 방법 설명용이다.
