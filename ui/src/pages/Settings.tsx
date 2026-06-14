import { useEffect, useState } from "react";
import { api } from "../api";
import type { AppSettings } from "../api";
import { Topbar } from "../components/ui.tsx";

export default function Settings() {
  const [settings, setSettings] = useState<AppSettings | null>(null);

  useEffect(() => {
    api.getSettings().then(setSettings);
  }, []);

  if (!settings) return <div className="content">Loading...</div>;

  return (
    <>
      <Topbar title="Settings" />
      <div className="content">
        <p className="muted" style={{ marginTop: 0 }}>
          Read-only view of the current server configuration.
        </p>

        <div className="card">
          <div className="card-head">
            <h2>Database</h2>
            <span className="type-tag">{settings.database.backend}</span>
          </div>
          <div className="settings-grid">
            <div className="settings-item">
              <span className="muted">Backend</span>
              <span>{settings.database.backend}</span>
            </div>
            <div className="settings-item">
              <span className="muted">Location</span>
              <span className="path">{settings.database.location}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h2>Endpoint status thresholds</h2>
          </div>
          <div className="settings-grid">
            <div className="settings-item">
              <span className="muted">Stale after</span>
              <span>{settings.thresholds.stale_minutes} minutes</span>
            </div>
            <div className="settings-item">
              <span className="muted">Inactive after</span>
              <span>{settings.thresholds.inactive_hours} hours</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h2>Dashboard</h2>
          </div>
          <div className="settings-grid">
            <div className="settings-item">
              <span className="muted">Auto-refresh interval</span>
              <span>{settings.dashboard.refresh_seconds === 0 ? "Disabled" : `${settings.dashboard.refresh_seconds}s`}</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
