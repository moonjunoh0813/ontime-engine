import { useMemo, useState } from "react";
import PlacePicker from "../components/PlacePicker.jsx";

const TIME_RE = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

function RouteDiagram() {
  return (
    <svg viewBox="0 0 360 420" className="route-svg" role="img" aria-label="노선도">
      <line x1="180" y1="40" x2="125" y2="115" className="dash-line" />
      <line x1="125" y1="115" x2="235" y2="115" className="solid-line" />
      <line x1="235" y1="115" x2="165" y2="185" className="dash-line" />
      <line x1="165" y1="185" x2="235" y2="185" className="solid-line" />
      <line x1="235" y1="185" x2="125" y2="255" className="dash-line" />
      <line x1="125" y1="255" x2="235" y2="255" className="solid-line" />
      <line x1="235" y1="255" x2="180" y2="335" className="dash-line" />

      <circle cx="180" cy="35" r="16" className="dark-node" />
      <circle cx="125" cy="115" r="14" className="light-node" />
      <circle cx="235" cy="115" r="14" className="light-node" />
      <circle cx="125" cy="185" r="14" className="light-node" />
      <circle cx="235" cy="185" r="14" className="light-node" />
      <circle cx="125" cy="255" r="14" className="light-node" />
      <circle cx="235" cy="255" r="14" className="light-node" />
      <circle cx="180" cy="340" r="16" className="dark-node" />

      <text x="180" y="40" textAnchor="middle" className="dark-text">1</text>
      <text x="125" y="120" textAnchor="middle" className="light-text">2</text>
      <text x="235" y="120" textAnchor="middle" className="light-text">3</text>
      <text x="125" y="190" textAnchor="middle" className="light-text">4</text>
      <text x="235" y="190" textAnchor="middle" className="light-text">5</text>
      <text x="125" y="260" textAnchor="middle" className="light-text">6</text>
      <text x="235" y="260" textAnchor="middle" className="light-text">7</text>
      <text x="180" y="345" textAnchor="middle" className="dark-text">8</text>

      <text x="165" y="95" textAnchor="middle" className="route-note">도보 (8분)</text>
      <text x="180" y="105" textAnchor="middle" className="route-link">지하철 (22분)</text>
      <text x="195" y="165" textAnchor="middle" className="route-note">도보 (10분)</text>
      <text x="190" y="176" textAnchor="middle" className="route-link">버스 (15분)</text>
      <text x="180" y="236" textAnchor="middle" className="route-note">도보 (5분)</text>
      <text x="180" y="247" textAnchor="middle" className="route-link">버스 (15분)</text>
      <text x="205" y="306" textAnchor="middle" className="route-note">도보 (5분)</text>

      <text x="86" y="120" className="node-label">미금역</text>
      <text x="252" y="120" className="node-label">강남역</text>
      <text x="88" y="190" className="node-label">학교</text>
      <text x="252" y="190" className="node-label">정류장B</text>
      <text x="88" y="260" className="node-label">정류장C</text>
      <text x="252" y="260" className="node-label">정류장B</text>
      <text x="168" y="360" className="node-label">학교</text>
    </svg>
  );
}

export default function RouteSettings({ settings, placeOptions, onBack, onSave }) {
  const [origin, setOrigin] = useState(settings.origin);
  const [destination, setDestination] = useState(settings.destination);
  const [destinationTime, setDestinationTime] = useState(settings.destinationTime);
  const [pickerTarget, setPickerTarget] = useState(null);

  const isSupportedRoute = origin === "집" && destination === "학교";
  const isValidTime = TIME_RE.test(destinationTime);

  const blockerMessage = useMemo(() => {
    if (!isSupportedRoute) {
      return "현재 MVP는 집→학교만 지원합니다.";
    }
    if (!isValidTime) {
      return "목표 시간을 HH:MM 형식으로 설정해주세요.";
    }
    return "";
  }, [isSupportedRoute, isValidTime]);

  const handleSelectPlace = (value) => {
    if (pickerTarget === "origin") {
      setOrigin(value);
    }
    if (pickerTarget === "destination") {
      setDestination(value);
    }
  };

  return (
    <main className="phone-frame">
      <section className="settings-card">
        <div className="settings-top">
          <button type="button" className="ghost-btn" onClick={onBack}>
            ← 뒤로
          </button>
          <h1>Route Settings</h1>
        </div>

        <div className="field-row">
          <label className="field-block">
            <span>출발지</span>
            <button
              type="button"
              className="picker-field"
              onClick={() => setPickerTarget("origin")}
            >
              {origin}
            </button>
          </label>
          <label className="field-block">
            <span>도착지</span>
            <button
              type="button"
              className="picker-field"
              onClick={() => setPickerTarget("destination")}
            >
              {destination}
            </button>
          </label>
        </div>

        <label className="field-block time-block">
          <span>목표 달성 시간</span>
          <input
            type="time"
            value={destinationTime}
            onChange={(event) => setDestinationTime(event.target.value)}
            step="60"
          />
        </label>

        {blockerMessage ? <p className="error-line">{blockerMessage}</p> : null}

        <section className="route-card">
          <RouteDiagram />
        </section>

        <button
          type="button"
          className="save-btn"
          disabled={Boolean(blockerMessage)}
          onClick={() => onSave({ origin, destination, destinationTime })}
        >
          저장하고 돌아가기
        </button>
      </section>

      <PlacePicker
        open={Boolean(pickerTarget)}
        title={pickerTarget === "origin" ? "출발지 선택" : "도착지 선택"}
        options={placeOptions}
        onSelect={handleSelectPlace}
        onClose={() => setPickerTarget(null)}
      />
    </main>
  );
}
