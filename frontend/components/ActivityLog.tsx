'use client';

import { useState, useEffect } from 'react';
import { Activity, Clock, Plus, Minus, Edit, Database } from 'lucide-react';
import { formatTimestamp, formatRelativeTime } from '@/lib/utils';
import { FlightVaultAPI } from '@/lib/api';

interface ActivityLogProps {
  table: string;
}

interface ActivityEntry {
  timestamp: string;
  change_count: number;
  changes: any[];
  has_mass_changes: boolean;
}

export default function ActivityLog({ table }: ActivityLogProps) {
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadActivities = async () => {
      setLoading(true);
      try {
        const data = await FlightVaultAPI.getTimeline(table, 168) as { timeline: ActivityEntry[] }; // 7 days
        setActivities(data.timeline || []);
      } catch (error) {
        console.error('Failed to load activities:', error);
      } finally {
        setLoading(false);
      }
    };

    loadActivities();
  }, [table]);

  const getActivityIcon = (entry: ActivityEntry) => {
    if (entry.has_mass_changes) return Minus;
    if (entry.change_count > 10) return Edit;
    if (entry.change_count > 0) return Plus;
    return Database;
  };

  const getActivityColor = (entry: ActivityEntry) => {
    if (entry.has_mass_changes) return 'text-danger-600 bg-danger-100';
    if (entry.change_count > 10) return 'text-warning-600 bg-warning-100';
    if (entry.change_count > 0) return 'text-success-600 bg-success-100';
    return 'text-gray-600 bg-gray-100';
  };

  const getActivityDescription = (entry: ActivityEntry) => {
    if (entry.has_mass_changes) return 'Mass deletion detected';
    if (entry.change_count > 10) return 'Multiple records modified';
    if (entry.change_count > 0) return `${entry.change_count} records changed`;
    return 'No changes';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Activity className="w-6 h-6 text-primary-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Activity Log</h1>
            <p className="text-gray-500">Recent database changes and events</p>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Activity Timeline */}
      {!loading && (
        <div className="card">
          <div className="space-y-4">
            {activities.length > 0 ? (
              activities.map((entry, index) => {
                const Icon = getActivityIcon(entry);
                const colorClass = getActivityColor(entry);
                
                return (
                  <div key={index} className="flex items-start space-x-4 p-4 hover:bg-gray-50 rounded-lg transition-colors">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${colorClass}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900">
                          {getActivityDescription(entry)}
                        </p>
                        <div className="flex items-center space-x-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{formatRelativeTime(entry.timestamp)}</span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-500 mt-1">
                        {formatTimestamp(entry.timestamp)}
                      </p>
                      
                      {entry.changes.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {entry.changes.slice(0, 3).map((change, changeIndex) => (
                            <div key={changeIndex} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                              {change.name || `Record ID: ${change[Object.keys(change)[0]]}`}
                            </div>
                          ))}
                          {entry.changes.length > 3 && (
                            <div className="text-xs text-gray-500">
                              ... and {entry.changes.length - 3} more changes
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12">
                <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Activity</h3>
                <p className="text-gray-500">No database changes detected in the selected time period.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}