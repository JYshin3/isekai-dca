# ⚔ 이세계 DCA — Adaptive DCA Dashboard

## 목표: 월 $2,000 × 36개월 → $500,000

---

## 설치 방법

### 1. Python 환경 준비
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 맥 미니에서 자동 실행 설정

### 자동 시작 (LaunchAgent)
```bash
mkdir -p ~/Library/LaunchAgents
```

아래 내용으로 `~/Library/LaunchAgents/com.isekai.dca.plist` 파일 생성:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.isekai.dca</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/streamlit</string>
        <string>run</string>
        <string>/path/to/isekai_dca/app.py</string>
        <string>--server.port=8501</string>
        <string>--server.headless=true</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/isekai_dca</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.isekai.dca.plist
```

로컬 네트워크에서 `http://맥미니IP:8501` 로 접속 가능

---

## 파일 구조
```
isekai_dca/
├── app.py              # 메인 Streamlit 앱
├── portfolio.json      # 포트폴리오 데이터 (자동 생성)
├── requirements.txt    # 패키지 목록
└── README.md
```

---

## 포트폴리오 설정 방법

1. 앱 실행 후 왼쪽 사이드바 클릭
2. "보유 주식 입력" 펼치기
3. 각 종목별 보유 주수 & 평균 단가 입력
4. 투자 시작일 입력
5. "💾 저장" 버튼 클릭

---

## 우라늄 가격 업데이트

주 1회 사이드바에서 수동 업데이트:
- 참고 사이트: https://www.cameco.com/invest/markets/uranium-price
- 또는 UxC: https://www.uxc.com

---

## 지표 파라미터 요약

| 종목  | RSI | StochRSI | MACD       | BB  | ATR | ADX |
|-------|-----|----------|------------|-----|-----|-----|
| GOOGL | 14  | 14/14    | 12,26,9    | 2.0 | 14  | 14  |
| IREN  | 20  | 20/10    | 20,40,9    | 2.5 | 20  | 20  |
| NXE   | 20  | 20/10    | 20,40,9    | 2.0 | 20  | 20  |
| MU    | 20  | 20/10    | 24,52,9    | 2.5 | 20  | 20  |
| IONQ  | 14  | 14/14    | 24,52,9    | 2.0 | 14  | 14  |
