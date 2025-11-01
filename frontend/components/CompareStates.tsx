'use client';

import { useState, useEffect } from 'react';
import { GitCompare, Plus, Minus, Edit, Calendar } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';
import { FlightVaultAPI } from '@/lib/api';
import { DiffResult, ChangeDetail } from '@/types';

interface CompareStatesProps {
  table: string;
}

export default function CompareStates({ table }: CompareStatesProps) {
  const [beforeTime, setBeforeTime] = useState('');
  const [afterTime, setAfterTime] = useState('');
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Set default times
    const now = new Date();
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);
    
    setAfterTime(now.toISOString().slice(0, 16));
    setBeforeTime(twoHoursAgo.toISOString().slice(0, 16));
  }, []);

  const loadDiff = async () => {
    if (!beforeTime || !afterTime) return;
    
    setLoading(true);
    try {
      const data = await FlightVaultAPI.getDiff(table, beforeTime, afterTime) as { diff: DiffResult };
      setDiff(data.diff);
    } catch (error) {
      console.error('Failed to load diff:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (beforeTime && afterTime) {
      loadDiff();
    }
  }, [beforeTime, afterTime, table]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <GitCompare className="w-6 h-6 text-primary-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Compare States</h1>
            <p className="text-gray-500">Side-by-side comparison of database states</p>
          </div>
        </div>
      </div>

      {/* Time Selection */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Before (Earlier State)
            </label>
            <div className="flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-gray-400" />
              <input
                type="datetime-local"
                value={beforeTime}
                onChange={(e) => setBeforeTime(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              After (Later State)
            </label>
            <div className="flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-gray-400" />
              <input
                type="datetime-local"
                value={afterTime}
                onChange={(e) => setAfterTime(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Diff Results */}
      {diff && !loading && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Deleted Records */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-danger-100 rounded-lg flex items-center justify-center">
                <Minus className="w-5 h-5 text-danger-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Deleted</h3>
                <p className="text-sm text-gray-500">{diff.summary.total_deleted} records</p>
              </div>
            </div>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {diff.deleted.slice(0, 20).map((record, index) => (
                <div key={index} className="p-3 bg-danger-50 border border-danger-200 rounded-lg">
                  <div className="font-medium text-danger-900">
                    {record.name || `ID: ${record[Object.keys(record)[0]]}`}
                  </div>
                  {record.city && (
                    <div className="text-sm text-danger-700">{record.city}, {record.country}</div>
                  )}
                </div>
              ))}
              {diff.deleted.length > 20 && (
                <div className="text-sm text-gray-500 text-center py-2">
                  ... and {diff.deleted.length - 20} more
                </div>
              )}
            </div>
          </div>

          {/* Added Records */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
                <Plus className="w-5 h-5 text-success-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Added</h3>
                <p className="text-sm text-gray-500">{diff.summary.total_added} records</p>
              </div>
            </div>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {diff.added.slice(0, 20).map((record, index) => (
                <div key={index} className="p-3 bg-success-50 border border-success-200 rounded-lg">
                  <div className="font-medium text-success-900">
                    {record.name || `ID: ${record[Object.keys(record)[0]]}`}
                  </div>
                  {record.city && (
                    <div className="text-sm text-success-700">{record.city}, {record.country}</div>
                  )}
                </div>
              ))}
              {diff.added.length > 20 && (
                <div className="text-sm text-gray-500 text-center py-2">
                  ... and {diff.added.length - 20} more
                </div>
              )}
            </div>
          </div>

          {/* Modified Records */}
          <div className="card">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-warning-100 rounded-lg flex items-center justify-center">
                <Edit className="w-5 h-5 text-warning-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Modified</h3>
                <p className="text-sm text-gray-500">{diff.summary.total_modified} records</p>
              </div>
            </div>
            
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {diff.modified.slice(0, 20).map((record, index) => (
                <div key={index} className="p-3 bg-warning-50 border border-warning-200 rounded-lg">
                  <div className="font-medium text-warning-900 mb-2">
                    {record.after.name || `ID: ${record.after[Object.keys(record.after)[0]]}`}
                  </div>
                  <div className="space-y-1">
                    {record.changes.slice(0, 3).map((change: ChangeDetail, changeIndex) => (
                      <div key={changeIndex} className="text-xs">
                        <span className="font-medium text-warning-800">{change.field}:</span>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="px-2 py-1 bg-danger-100 text-danger-700 rounded text-xs">
                            {String(change.before).slice(0, 20)}
                          </span>
                          <span className="text-gray-400">→</span>
                          <span className="px-2 py-1 bg-success-100 text-success-700 rounded text-xs">
                            {String(change.after).slice(0, 20)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {diff.modified.length > 20 && (
                <div className="text-sm text-gray-500 text-center py-2">
                  ... and {diff.modified.length - 20} more
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Summary */}
      {diff && !loading && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-danger-50 rounded-lg">
              <div className="text-2xl font-bold text-danger-600">{diff.summary.total_deleted}</div>
              <div className="text-sm text-danger-700">Records Deleted</div>
            </div>
            <div className="text-center p-4 bg-success-50 rounded-lg">
              <div className="text-2xl font-bold text-success-600">{diff.summary.total_added}</div>
              <div className="text-sm text-success-700">Records Added</div>
            </div>
            <div className="text-center p-4 bg-warning-50 rounded-lg">
              <div className="text-2xl font-bold text-warning-600">{diff.summary.total_modified}</div>
              <div className="text-sm text-warning-700">Records Modified</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}