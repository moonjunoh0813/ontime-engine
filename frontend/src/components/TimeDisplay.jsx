function toDisplayParts(time) {
  if (!time || !/^\d{2}:\d{2}$/.test(time)) {
    return { hourMinute: "--:--", ampm: "" };
  }

  const [hourText, minute] = time.split(":");
  const hour = Number(hourText);
  const ampm = hour >= 12 ? "PM" : "AM";
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;

  return {
    hourMinute: `${String(hour12).padStart(2, "0")}:${minute}`,
    ampm,
  };
}

export default function TimeDisplay({ time }) {
  const { hourMinute, ampm } = toDisplayParts(time);

  return (
    <div className="time-display" aria-label={`추천 출발 시간 ${time}`}>
      <span className="time-display-main">{hourMinute}</span>
      {ampm ? <span className="time-display-ampm">{ampm}</span> : null}
    </div>
  );
}
