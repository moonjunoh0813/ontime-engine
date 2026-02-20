import { useCallback, useEffect, useMemo, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import RouteSettings from "./pages/RouteSettings.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const STORAGE_KEY = "ontime.route.settings";
const TIME_RE = /^(?:[01]\d|2[0-3]):[0-5]\d$/;
const PLACE_OPTIONS = ["집", "학교"];

const DEFAULT_SETTINGS = {
  origin: "집",
  destination: "학교",
  destinationTime: "09:00",
};

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return DEFAULT_SETTINGS;
    }

    const parsed = JSON.parse(raw);
    const origin = PLACE_OPTIONS.includes(parsed.origin)
      ? parsed.origin
      : DEFAULT_SETTINGS.origin;
    const destination = PLACE_OPTIONS.includes(parsed.destination)
      ? parsed.destination
      : DEFAULT_SETTINGS.destination;
    const destinationTime = TIME_RE.test(parsed.destinationTime)
      ? parsed.destinationTime
      : DEFAULT_SETTINGS.destinationTime;

    return { origin, destination, destinationTime };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

function toUserError(err) {
  if (!(err instanceof Error)) {
    return "네트워크 오류입니다.";
  }

  if (err.message === "Failed to fetch") {
    return `서버에 연결할 수 없습니다. 백엔드를 실행했는지 확인해주세요. (${API_BASE})`;
  }

  return err.message;
}

export default function App() {
  const [screen, setScreen] = useState("dashboard");
  const [settings, setSettings] = useState(loadSettings);
  const [recommendedTime, setRecommendedTime] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isSupportedRoute =
    settings.origin === "집" && settings.destination === "학교";

  const computeRecommendation = useCallback(async (destinationTime) => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/compute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ destination_time: destinationTime }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail =
          typeof payload.detail === "string"
            ? payload.detail
            : "요청에 실패했습니다.";
        throw new Error(`${detail} (HTTP ${response.status})`);
      }

      if (typeof payload.recommended_departure_time === "string") {
        setRecommendedTime(payload.recommended_departure_time);
      } else {
        throw new Error("추천 출발 시간이 응답에 없습니다.");
      }
    } catch (err) {
      setError(toUserError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  useEffect(() => {
    if (screen !== "dashboard") {
      return;
    }

    if (!TIME_RE.test(settings.destinationTime)) {
      setError("목표 시간 형식이 올바르지 않습니다.");
      return;
    }

    if (!isSupportedRoute) {
      setError("현재 MVP는 집→학교만 지원합니다.");
      return;
    }

    computeRecommendation(settings.destinationTime);
  }, [
    screen,
    settings.destinationTime,
    settings.origin,
    settings.destination,
    isSupportedRoute,
    computeRecommendation,
  ]);

  const onSaveSettings = (nextSettings) => {
    setSettings(nextSettings);
    setScreen("dashboard");
  };

  const dashboardError = useMemo(() => {
    if (!isSupportedRoute) {
      return "현재 MVP는 집→학교만 지원합니다.";
    }
    return error;
  }, [error, isSupportedRoute]);

  return (
    <div className="app-shell">
      {screen === "dashboard" ? (
        <Dashboard
          settings={settings}
          recommendedTime={recommendedTime}
          loading={loading}
          error={dashboardError}
          onOpenSettings={() => setScreen("settings")}
        />
      ) : (
        <RouteSettings
          settings={settings}
          placeOptions={PLACE_OPTIONS}
          onBack={() => setScreen("dashboard")}
          onSave={onSaveSettings}
        />
      )}
    </div>
  );
}
