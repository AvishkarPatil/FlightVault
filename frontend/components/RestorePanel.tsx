'use client';

import { useState, useEffect } from 'react';
import { Brain, Zap, AlertTriangle, CheckCircle, Clock, BarChart3, Timer, Target, Calendar, Settings, RotateCcw } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';
import { FlightVaultAPI } from '@/lib/api';
import { RestoreSuggestion, RestoreResult } from '@/types';

interface RestorePanelProps {
  table: string;
  onRestoreComplete: () => void;
}

export default function RestorePanel({ table, onRestoreComplete }: RestorePanelProps) {
  const [suggestion, setSuggestion] = useState<RestoreSuggestion | null>(null);
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [result, setResult] = useState<RestoreResult | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [restoreMode, setRestoreMode] = useState<'smart' | 'manual'>('smart');
  const [customTimestamp, setCustomTimestamp] = useState<string>('');
  const [manualPreview, setManualPreview] = useState<RestoreResult | null>(null);

  const getSuggestion = async () => {
    setLoading(true);
    setResult(null);
    try {
      const data = await FlightVaultAPI.getSuggestRestore(table) as RestoreSuggestion;
      setSuggestion(data);
    } catch (error) {
      console.error('Failed to get suggestion:', error);
    } finally {
      setLoading(false);
    }
  };

  const previewRestore = async (timestamp?: string) => {
    const targetTimestamp = timestamp || (suggestion?.suggested_timestamp);
    console.log('Preview restore called with:', { timestamp, targetTimestamp, table });
    if (!targetTimestamp) {
      console.log('No target timestamp, returning');
      return;
    }
    
    setLoading(true);
    try {
      console.log('Making API call for preview...');
      const data = await FlightVaultAPI.executeRestore(
        table,
        targetTimestamp,
        true // dry run
      ) as RestoreResult;
      console.log('Preview API response:', data);
      
      if (timestamp) {
        console.log('Setting manual preview');
        setManualPreview({ ...data, dry_run: true });
      } else {
        console.log('Setting smart result');
        setResult({ ...data, dry_run: true });
      }
    } catch (error) {
      console.error('Preview error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      const errorResult = { 
        success: false, 
        error: errorMessage,
        dry_run: true 
      };
      
      if (timestamp) {
        setManualPreview(errorResult);
      } else {
        setResult(errorResult);
      }
    } finally {
      setLoading(false);
    }
  };

  const executeRestore = async (timestamp?: string) => {
    const targetTimestamp = timestamp || (suggestion?.suggested_timestamp);
    if (!targetTimestamp) return;
    
    setRestoring(true);
    try {
      const data = await FlightVaultAPI.executeRestore(
        table,
        targetTimestamp,
        false // actual restore
      ) as RestoreResult;
      setResult(data);
      setManualPreview(null);
      setShowConfirm(false);
      
      if (data.success) {
        setTimeout(() => {
          onRestoreComplete();
        }, 1000);
        onRestoreComplete();
      }
    } catch (error) {
      console.error('Failed to execute restore:', error);
    } finally {
      setRestoring(false);
    }
  };

  useEffect(() => {
    getSuggestion();
  }, [table]);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-success-600';
    if (confidence >= 70) return 'text-warning-600';
    return 'text-danger-600';
  };

  const getConfidenceBg = (confidence: number) => {
    if (confidence >= 90) return 'bg-success-50 border-success-200';
    if (confidence >= 70) return 'bg-warning-50 border-warning-200';
    return 'bg-danger-50 border-danger-200';
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Brain className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Recovery Center</h2>
            <p className="text-sm text-gray-500">Intelligent restore point analysis</p>
          </div>
        </div>
        
        {/* Mode Toggle */}
        <div className="flex items-center space-x-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => {
              setRestoreMode('smart');
              setManualPreview(null);
            }}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              restoreMode === 'smart'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Brain className="w-4 h-4 inline mr-1" />
            Smart
          </button>
          <button
            onClick={() => {
              setRestoreMode('manual');
              setResult(null);
            }}
            className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              restoreMode === 'manual'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Calendar className="w-4 h-4 inline mr-1" />
            Manual
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && !suggestion && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Smart Suggestion */}
      {restoreMode === 'smart' && suggestion && (
        <div className={`p-4 rounded-lg border-2 mb-6 ${getConfidenceBg(suggestion.confidence_percentage)}`}>
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-primary-600" />
              <h3 className="font-medium text-gray-900">Optimal Restore Point</h3>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2 w-20">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 ${
                    suggestion.confidence_percentage >= 90 ? 'bg-success-500' :
                    suggestion.confidence_percentage >= 70 ? 'bg-warning-500' : 'bg-danger-500'
                  }`}
                  style={{ width: `${suggestion.confidence_percentage}%` }}
                />
              </div>
              <span className={`text-sm font-medium ${getConfidenceColor(suggestion.confidence_percentage)}`}>
                {suggestion.confidence_percentage}%
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-900">
                {formatTimestamp(suggestion.suggested_timestamp)}
              </span>
            </div>
            
            <p className="text-sm text-gray-700">
              💡 {suggestion.reason}
            </p>

            {suggestion.warnings.length > 0 && (
              <div className="mt-3 p-2 bg-warning-50 border border-warning-200 rounded">
                <div className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-warning-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-warning-800">Warnings:</p>
                    <ul className="text-sm text-warning-700 mt-1 space-y-1">
                      {suggestion.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Timestamp Input */}
      {restoreMode === 'manual' && (
        <div className="p-4 border-2 border-gray-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-4">
            <Calendar className="w-5 h-5 text-primary-600" />
            <h3 className="font-medium text-gray-900">Manual Timestamp Selection</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Restore Point
              </label>
              <input
                type="datetime-local"
                value={customTimestamp}
                onChange={(e) => setCustomTimestamp(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                max={new Date().toISOString().slice(0, 16)}
              />
              <p className="text-xs text-gray-500 mt-1">
                Select any point in time to restore the database to that exact state
              </p>
            </div>
            
            {customTimestamp && (
              <div className="flex space-x-3">
                <button
                  onClick={() => previewRestore(customTimestamp)}
                  disabled={loading}
                  className="btn-secondary flex-1"
                >
                  {loading ? 'Previewing...' : 'Preview Restore'}
                </button>
                <button
                  onClick={() => setShowConfirm(true)}
                  disabled={loading || restoring}
                  className="btn-danger flex-1 flex items-center justify-center space-x-2"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>RESTORE NOW</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Manual Preview Results */}
      {manualPreview && manualPreview.dry_run && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-blue-900">Manual Restore Preview</h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-blue-100 rounded-lg">
              <div className="text-lg font-bold text-blue-900">{manualPreview.records_to_restore?.toLocaleString()}</div>
              <div className="text-xs text-blue-700">Records to Restore</div>
            </div>
            {manualPreview.changes_preview && (
              <>
                <div className="text-center p-3 bg-success-100 rounded-lg">
                  <div className="text-lg font-bold text-success-900">{manualPreview.changes_preview.will_add}</div>
                  <div className="text-xs text-success-700">Will Add</div>
                </div>
                <div className="text-center p-3 bg-warning-100 rounded-lg">
                  <div className="text-lg font-bold text-warning-900">{manualPreview.changes_preview.will_update}</div>
                  <div className="text-xs text-warning-700">Will Update</div>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center space-x-2 text-sm text-blue-800">
            <Timer className="w-4 h-4" />
            <span>Target: {formatTimestamp(customTimestamp)}</span>
          </div>
        </div>
      )}

      {/* Manual Error Result */}
      {manualPreview && !manualPreview.dry_run && !manualPreview.success && (
        <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-danger-600" />
            <h4 className="font-medium text-danger-900">Manual Preview Failed</h4>
          </div>
          <p className="text-sm text-danger-800">{manualPreview.error || 'Unknown error occurred'}</p>
        </div>
      )}

      {/* Smart Preview Results */}
      {restoreMode === 'smart' && result && result.dry_run && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-3">
            <BarChart3 className="w-5 h-5 text-blue-600" />
            <h4 className="font-medium text-blue-900">Recovery Impact Analysis</h4>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-blue-100 rounded-lg">
              <div className="text-lg font-bold text-blue-900">{result.records_to_restore?.toLocaleString()}</div>
              <div className="text-xs text-blue-700">Records to Restore</div>
            </div>
            {result.changes_preview && (
              <>
                <div className="text-center p-3 bg-success-100 rounded-lg">
                  <div className="text-lg font-bold text-success-900">{result.changes_preview.will_add}</div>
                  <div className="text-xs text-success-700">Will Add</div>
                </div>
                <div className="text-center p-3 bg-warning-100 rounded-lg">
                  <div className="text-lg font-bold text-warning-900">{result.changes_preview.will_update}</div>
                  <div className="text-xs text-warning-700">Will Update</div>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center space-x-2 text-sm text-blue-800">
            <Timer className="w-4 h-4" />
            <span>Estimated recovery time: &lt; 1 second</span>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && result.success && !result.dry_run && (
        <div className="p-4 bg-success-50 border border-success-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-success-600" />
            <h4 className="font-medium text-success-900">Restore Successful!</h4>
          </div>
          <div className="space-y-1 text-sm text-success-800">
            <p>• Restored: {result.records_restored?.toLocaleString()} records</p>
            <p>• Final count: {result.final_count?.toLocaleString()} records</p>
            <p>• Execution time: {result.execution_time}</p>
          </div>
        </div>
      )}

      {/* Error Result */}
      {result && !result.dry_run && !result.success && (
        <div className="p-4 bg-danger-50 border border-danger-200 rounded-lg mb-6">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-danger-600" />
            <h4 className="font-medium text-danger-900">
              {result.dry_run ? 'Preview Failed' : 'Restore Failed'}
            </h4>
          </div>
          <p className="text-sm text-danger-800">{result.error || 'Unknown error occurred'}</p>
          {result.dry_run && (
            <p className="text-xs text-danger-700 mt-2">
              Check that the API server is running and the timestamp is valid.
            </p>
          )}
        </div>
      )}

      {/* Smart Mode Action Buttons */}
      {restoreMode === 'smart' && (
        <div className="flex space-x-3">
          <button
            onClick={getSuggestion}
            disabled={loading}
            className="btn-secondary flex-1"
          >
            {loading ? 'Getting Suggestion...' : 'Refresh Suggestion'}
          </button>

          {suggestion && (
            <button
              onClick={() => previewRestore()}
              disabled={loading}
              className="btn-secondary flex-1"
            >
              {loading ? 'Previewing...' : 'Preview Restore'}
            </button>
          )}

          {suggestion && (
            <button
              onClick={() => setShowConfirm(true)}
              disabled={loading || restoring || suggestion.confidence_percentage < 50}
              className="btn-danger flex-1 flex items-center justify-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>RESTORE NOW</span>
            </button>
          )}
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-danger-600" />
              <h3 className="text-lg font-semibold text-gray-900">Confirm Restore</h3>
            </div>
            
            <p className="text-gray-700 mb-6">
              This will restore the database to {formatTimestamp(
                restoreMode === 'manual' ? customTimestamp : suggestion!.suggested_timestamp
              )}. This action cannot be undone.
            </p>
            
            <div className="flex space-x-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={() => executeRestore(
                  restoreMode === 'manual' ? customTimestamp : undefined
                )}
                disabled={restoring}
                className="btn-danger flex-1"
              >
                {restoring ? 'Restoring...' : 'Confirm Restore'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}