import React, { useEffect, useState } from 'react';

const ApiTest: React.FC = () => {
  const [status, setStatus] = useState<string>('Loading...');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const testApi = async () => {
      try {
        console.log('Testing API connection...');
        
        // Test system status
        const statusResponse = await fetch('http://localhost:8000/api/v1/system/status');
        console.log('Status response:', statusResponse);
        
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          console.log('Status data:', statusData);
          setStatus('Backend Connected ✅');
          
          // Test dashboard data
          const dashboardResponse = await fetch('http://localhost:8000/api/v1/analytics/dashboard');
          if (dashboardResponse.ok) {
            const dashboard = await dashboardResponse.json();
            console.log('Dashboard data:', dashboard);
            setDashboardData(dashboard);
          } else {
            setError('Dashboard API failed');
          }
        } else {
          setStatus('Backend Connection Failed ❌');
          setError(`Status: ${statusResponse.status}`);
        }
      } catch (err) {
        console.error('API Test Error:', err);
        setStatus('API Error ❌');
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    testApi();
  }, []);

  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', margin: '20px', borderRadius: '8px' }}>
      <h2>🔧 API Connection Test</h2>
      <p><strong>Status:</strong> {status}</p>
      
      {error && (
        <p style={{ color: 'red' }}><strong>Error:</strong> {error}</p>
      )}
      
      {dashboardData && (
        <div>
          <h3>📊 Dashboard Data</h3>
          <ul>
            <li><strong>Active Incidents:</strong> {dashboardData.active_incidents}</li>
            <li><strong>Today's Incidents:</strong> {dashboardData.todays_incidents}</li>
            <li><strong>Available Units:</strong> {dashboardData.available_units}</li>
            <li><strong>Total Units:</strong> {dashboardData.total_units}</li>
            <li><strong>Recent Alerts:</strong> {dashboardData.recent_alerts?.length || 0}</li>
            <li><strong>System Status:</strong> {dashboardData.system_status}</li>
          </ul>
          
          {dashboardData.recent_alerts?.length > 0 && (
            <div>
              <h4>Recent Alerts:</h4>
              {dashboardData.recent_alerts.slice(0, 3).map((alert: any, index: number) => (
                <div key={index} style={{ margin: '10px 0', padding: '10px', backgroundColor: 'white', borderRadius: '4px' }}>
                  <p><strong>{alert.alert_type}:</strong> {alert.description}</p>
                  <p><small>Severity: {alert.severity} | Status: {alert.status}</small></p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
        <p>This component tests direct API calls to verify backend connectivity.</p>
        <p>Check browser console for detailed logs.</p>
      </div>
    </div>
  );
};

export default ApiTest;
