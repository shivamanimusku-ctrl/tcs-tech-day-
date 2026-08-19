/**
 * Main Application Component — integrates Factory Health Bar, Role Switcher,
 * and Role-specific views (Plant Manager, Supervisor, Maintenance Team).
 */

import { useState, useEffect, useCallback } from 'react';
import FactoryHealthBar from './components/FactoryHealthBar';
import RoleSwitcher from './components/RoleSwitcher';
import PlantManagerView from './components/PlantManagerView';
import SupervisorView from './components/SupervisorView';
import MaintenanceView from './components/MaintenanceView';
import { api } from './api';

export default function App() {
  const [role, setRole] = useState('Plant Manager');
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [machines, setMachines] = useState([]);
  const [production, setProduction] = useState([]);
  const [quality, setQuality] = useState([]);
  const [orders, setOrders] = useState([]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reseeding, setReseeding] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setError(null);
      const [
        summaryData,
        alertsData,
        machinesData,
        prodData,
        qualData,
        ordersData,
        notesData,
      ] = await Promise.all([
        api.getDashboardSummary(),
        api.getAlerts(),
        api.getMachines(),
        api.getProduction(),
        api.getQuality(),
        api.getOrders(),
        api.getNotes(),
      ]);

      setSummary(summaryData);
      setAlerts(alertsData);
      setMachines(machinesData);
      setProduction(prodData);
      setQuality(qualData);
      setOrders(ordersData);
      setNotes(notesData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Could not connect to backend REST API. Please ensure the FastAPI server is running on http://localhost:8000.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Refresh interval every 15 seconds
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      await api.updateAlertStatus(alertId, newStatus);
      await loadData();
    } catch (err) {
      console.error('Failed to update alert status:', err);
      alert('Failed to update alert status');
    }
  };

  const handleReseed = async () => {
    if (!window.confirm('Reset database to default seed scenario?')) return;
    setReseeding(true);
    try {
      await api.reseed();
      await loadData();
    } catch (err) {
      console.error('Failed to reseed:', err);
      alert('Failed to reseed database');
    } finally {
      setReseeding(false);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="app-title">
          <div className="app-logo">⚡</div>
          <div>
            <h1>Production Disruption Early Warning System</h1>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-muted)' }}>
              Detect → Predict → Explain → Prioritize → Recommend → Escalate
            </div>
          </div>
        </div>

        <div className="header-controls">
          <button
            className="btn btn-reset"
            onClick={handleReseed}
            disabled={reseeding}
            title="Reset database to initial seed scenario"
          >
            {reseeding ? '↻ Resetting...' : '↻ Reset Seed Data'}
          </button>
          <RoleSwitcher currentRole={role} onRoleChange={setRole} />
        </div>
      </header>

      {/* Connection Error Banner */}
      {error && (
        <div className="error-message fade-in">
          {error}
        </div>
      )}

      {/* Factory Health Bar */}
      <FactoryHealthBar summary={summary} loading={loading} />

      {/* Role-based View Rendering */}
      <main>
        {role === 'Plant Manager' && (
          <PlantManagerView
            alerts={alerts}
            summary={summary}
            orders={orders}
            onStatusChange={handleStatusChange}
            loading={loading}
          />
        )}

        {role === 'Supervisor' && (
          <SupervisorView
            alerts={alerts}
            production={production}
            quality={quality}
            orders={orders}
            notes={notes}
            onStatusChange={handleStatusChange}
            loading={loading}
          />
        )}

        {role === 'Maintenance Team' && (
          <MaintenanceView
            alerts={alerts}
            machines={machines}
            onStatusChange={handleStatusChange}
            loading={loading}
          />
        )}
      </main>
    </div>
  );
}
