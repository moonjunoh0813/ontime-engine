import TimeDisplay from "../components/TimeDisplay.jsx";

function getSlackMinutes(recommendedTime) {
  if (!recommendedTime || !/^\d{2}:\d{2}$/.test(recommendedTime)) {
    return null;
  }

  const [hour, minute] = recommendedTime.split(":").map(Number);
  const targetMinutes = hour * 60 + minute;
  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  let diff = targetMinutes - nowMinutes;
  if (diff < 0) {
    diff += 24 * 60;
  }
  return diff;
}

export default function Dashboard({
  settings,
  recommendedTime,
  loading,
  error,
  onOpenSettings,
}) {
  const slackMinutes = getSlackMinutes(recommendedTime);

  return (
    <main className="phone-frame">
      <section className="dashboard-card">
        <header className="top-row">
          <div className="icon-chip">CAL</div>
          <p className="top-title">PREMIUM DASHBOARD</p>
          <div className="icon-chip">ALM</div>
        </header>

        <p className="section-kicker">RECOMMENDED DEPARTURE</p>
        <TimeDisplay time={recommendedTime || "--:--"} />
        <p className="trip-subtitle">학교로 출발</p>

        <div className="meta-row">
          <span className="meta-left">{settings.destinationTime} 도착 목표</span>
          <span className="meta-right">- 도착 예상</span>
        </div>

        <div className="down-dot">v</div>

        <section className="status-card">
          <p className="status-title">여유롭게 준비하세요.</p>
          <p className="status-subtitle">
            {slackMinutes === null
              ? "추천 시간 계산 중"
              : `집에서 ${slackMinutes}분 후 출발`}
          </p>
          <button type="button" className="eta-pill" disabled>
            버스 ETA 준비중
          </button>
          <p className="status-footnote">정거장 통행정보센터 제공중</p>
        </section>

        {loading ? <p className="loading-line">업데이트 중...</p> : null}
        {error ? <p className="error-line">{error}</p> : null}

        <button type="button" className="up-next" onClick={onOpenSettings}>
          <span>UP NEXT</span>
          <span className="arrow">{"->"}</span>
        </button>

        <div className="mini-grid">
          <article className="mini-card">
            <div className="mini-icon">AC</div>
            <p className="mini-title">학원</p>
            <p className="mini-time">13:15 출발</p>
          </article>
          <article className="mini-card">
            <div className="mini-icon">GY</div>
            <p className="mini-title">헬스장</p>
            <p className="mini-time">17:50 출발</p>
          </article>
        </div>
      </section>
    </main>
  );
}
