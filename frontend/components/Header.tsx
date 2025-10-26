'use client';

import { useState, useEffect } from 'react';
import { Database, Plane, Activity } from 'lucide-react';
import { FlightVaultAPI } from '@/lib/api';

export default function Header() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await FlightVaultAPI.getHealth();
        setIsConnected(true);
        
        const statsData = await FlightVaultAPI.get('/stats');
        setStats(statsData);
      } catch (error) {
        setIsConnected(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Page Title */}
          <div>
            <h1 className="text-xl font-bold text-gray-900">Database Recovery Dashboard</h1>
            <p className="text-sm text-gray-500">Real-time temporal database monitoring</p>
          </div>

          {/* Status Indicators */}
          <div className="flex items-center space-x-6">
            {/* Database Status */}
            <div className="flex items-center space-x-2">
              <Database className="w-5 h-5 text-gray-400" />
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    isConnected === null
                      ? 'bg-gray-400'
                      : isConnected
                      ? 'bg-success-500'
                      : 'bg-danger-500'
                  }`}
                />
                <span className="text-sm font-medium text-gray-700">
                  {isConnected === null
                    ? 'Checking...'
                    : isConnected
                    ? 'Connected'
                    : 'Disconnected'}
                </span>
              </div>
            </div>

            {/* Stats */}
            {stats && (
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <div className="flex items-center space-x-1">
                  <Activity className="w-4 h-4" />
                  <span>{stats.total_records?.toLocaleString()} records</span>
                </div>
                <div className="flex items-center space-x-1">
                  <span className="w-2 h-2 bg-warning-500 rounded-full" />
                  <span>{stats.total_recent_changes} changes</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}