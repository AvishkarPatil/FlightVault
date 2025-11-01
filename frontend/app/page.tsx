'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import TimelineSlider from '@/components/TimelineSlider';
import DataDisplay from '@/components/DataDisplay';
import RestorePanel from '@/components/RestorePanel';
import CompareStates from '@/components/CompareStates';
import ActivityLog from '@/components/ActivityLog';
import { FlightVaultAPI } from '@/lib/api';
import { TableInfo } from '@/types';

export default function Home() {
  const [activeTab, setActiveTab] = useState('timeline');
  const [selectedTable, setSelectedTable] = useState('airports');
  const [currentTimestamp, setCurrentTimestamp] = useState(new Date().toISOString());
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const loadTables = async () => {
      try {
        const data = await FlightVaultAPI.getTables() as { tables: TableInfo[] };
        setTables(data.tables || []);
      } catch (error) {
        console.error('Failed to load tables:', error);
      }
    };

    loadTables();
  }, [refreshKey]);

  const handleRestoreComplete = () => {
    // Refresh data after restore
    setRefreshKey(prev => prev + 1);
    setCurrentTimestamp(new Date().toISOString());
  };

  const selectedTableInfo = tables.find(t => t.name === selectedTable);

  const renderContent = () => {
    switch (activeTab) {
      case 'timeline':
        return (
          <div className="space-y-8">
            {/* Timeline Slider - The Signature Feature */}
            <TimelineSlider
              table={selectedTable}
              onTimestampChange={setCurrentTimestamp}
              currentTimestamp={currentTimestamp}
            />
            
            {/* Data Display */}
            <DataDisplay
              key={`${selectedTable}-${currentTimestamp}-${refreshKey}`}
              table={selectedTable}
              timestamp={currentTimestamp}
            />
          </div>
        );
      
      case 'data':
        return (
          <DataDisplay
            key={`data-${selectedTable}-${refreshKey}`}
            table={selectedTable}
            timestamp={new Date().toISOString()}
          />
        );
      
      case 'compare':
        return <CompareStates table={selectedTable} />;
      
      case 'restore':
        return (
          <RestorePanel
            key={`restore-${selectedTable}-${refreshKey}`}
            table={selectedTable}
            onRestoreComplete={handleRestoreComplete}
          />
        );
      
      case 'activity':
        return <ActivityLog table={selectedTable} />;
      
      case 'settings':
        return (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Database Configuration</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Connection Status</label>
                  <div className="p-3 bg-success-50 border border-success-200 rounded-lg">
                    <span className="text-success-800">✓ Connected to MariaDB</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Temporal Tables</label>
                  <div className="space-y-2">
                    {['airports', 'airlines', 'routes'].map(table => (
                      <div key={table} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm">{table}</span>
                        <span className="text-xs text-success-600">✓ System Versioning Enabled</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Display Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Records per page</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="25">25 records</option>
                    <option value="50">50 records</option>
                    <option value="100">100 records</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Timeline granularity</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="1">1 minute periods</option>
                    <option value="5">5 minute periods</option>
                    <option value="60">1 hour periods</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Recovery Settings</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Auto-detect disasters</label>
                    <p className="text-xs text-gray-500">Automatically suggest restore points</p>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Confirmation dialogs</label>
                    <p className="text-xs text-gray-500">Require confirmation before restore</p>
                  </div>
                  <input type="checkbox" defaultChecked className="rounded" />
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col ml-64">
        <Header />
        
        <main className="flex-1 p-8">
          {/* Table Selector */}
          <div className="mb-8">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">
                Table:
              </label>
              <select
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {tables.map((table) => (
                  <option key={table.name} value={table.name}>
                    {table.name} ({table.current_count.toLocaleString()} records)
                  </option>
                ))}
              </select>
              
              {selectedTableInfo && (
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>
                    Last change: {selectedTableInfo.last_change 
                      ? new Date(selectedTableInfo.last_change).toLocaleTimeString()
                      : 'None'
                    }
                  </span>
                  <span>
                    Recent changes: {selectedTableInfo.recent_changes || 0}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Dynamic Content */}
          {renderContent()}
        </main>
      </div>
    </div>
  );
}