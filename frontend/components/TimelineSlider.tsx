'use client';

import { useState, useEffect, useCallback } from 'react';
import { Clock, Calendar, AlertTriangle } from 'lucide-react';
import { formatTimestamp, sliderValueToTimestamp, timestampToSliderValue } from '@/lib/utils';
import { FlightVaultAPI } from '@/lib/api';
import { TimelineEntry } from '@/types';

interface TimelineSliderProps {
  table: string;
  onTimestampChange: (timestamp: string) => void;
  currentTimestamp: string;
}

export default function TimelineSlider({ table, onTimestampChange, currentTimestamp }: TimelineSliderProps) {
  const [sliderValue, setSliderValue] = useState(100); // 100 = now
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [hours] = useState(120);

  // Load timeline data
  useEffect(() => {
    const loadTimeline = async () => {
      try {
        const data = await FlightVaultAPI.getTimeline(table, hours) as { timeline: TimelineEntry[] };
        setTimeline(data.timeline || []);
      } catch (error) {
        console.error('Failed to load timeline:', error);
      }
    };

    loadTimeline();
  }, [table, hours]);

  // Update slider when external timestamp changes
  useEffect(() => {
    const newValue = timestampToSliderValue(currentTimestamp, hours);
    setSliderValue(newValue);
  }, [currentTimestamp, hours]);

  // Debounced timestamp change
  const debouncedTimestampChange = useCallback(
    debounce((value: number) => {
      const timestamp = sliderValueToTimestamp(value, hours);
      onTimestampChange(timestamp);
    }, 300),
    [hours, onTimestampChange]
  );

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setSliderValue(value);
    setLoading(true);
    debouncedTimestampChange(value);
    
    // Clear loading after a short delay
    setTimeout(() => setLoading(false), 500);
  };

  const getTimelineMarkers = () => {
    return timeline.map((entry, index) => {
      const entryTime = new Date(entry.timestamp);
      const now = new Date();
      const hoursBack = (now.getTime() - entryTime.getTime()) / (1000 * 60 * 60);
      const position = Math.max(0, Math.min(100, ((hours - hoursBack) / hours) * 100));

      return {
        position,
        entry,
        key: index,
      };
    });
  };

  const [currentTime, setCurrentTime] = useState('');
  const [isHistorical, setIsHistorical] = useState(false);
  
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const time = sliderValueToTimestamp(sliderValue, hours);
      setCurrentTime(time);
      setIsHistorical(sliderValue < 99);
    }
  }, [sliderValue, hours]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Clock className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Timeline Explorer</h2>
            <p className="text-sm text-gray-500">Navigate through {hours} hours of database history</p>
          </div>
        </div>
        
        {loading && (
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <div className="animate-spin w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full" />
            <span>Loading...</span>
          </div>
        )}
      </div>

      {/* Current Timestamp Display */}
      <div className={`mb-6 p-4 rounded-lg border-2 ${
        isHistorical 
          ? 'bg-warning-50 border-warning-200' 
          : 'bg-success-50 border-success-200'
      }`}>
        <div className="flex items-center space-x-3">
          {isHistorical ? (
            <AlertTriangle className="w-5 h-5 text-warning-600" />
          ) : (
            <Calendar className="w-5 h-5 text-success-600" />
          )}
          <div>
            <div className="flex items-center space-x-2">
              <span className={`text-sm font-medium ${
                isHistorical ? 'text-warning-800' : 'text-success-800'
              }`}>
                {isHistorical ? '⚠️ Historical View' : '✓ Current State'}
              </span>
              {isHistorical && (
                <button
                  onClick={() => {
                    setSliderValue(100);
                    onTimestampChange(new Date().toISOString());
                  }}
                  className="text-xs text-warning-600 hover:text-warning-700 underline"
                >
                  Go to Now
                </button>
              )}
            </div>
            <p className={`text-sm ${
              isHistorical ? 'text-warning-700' : 'text-success-700'
            }`}>
              {formatTimestamp(currentTime)}
            </p>
          </div>
        </div>
      </div>

      {/* Timeline Slider */}
      <div className="relative mb-4">
        <div className="flex justify-between text-xs text-gray-500 mb-2">
          <span>{hours}h ago</span>
          <span>Now</span>
        </div>
        
        <div className="relative">
          <input
            type="range"
            min="0"
            max="100"
            step="0.1"
            value={sliderValue}
            onChange={handleSliderChange}
            className="timeline-slider w-full"
          />
          
          {/* Timeline Markers */}
          <div className="absolute top-0 left-0 w-full h-2 pointer-events-none">
            {getTimelineMarkers().map(({ position, entry, key }) => (
              <div
                key={key}
                className="absolute top-0 transform -translate-x-1/2 cursor-pointer group pointer-events-auto"
                style={{ left: `${position}%` }}
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setSliderValue(position);
                  const timestamp = sliderValueToTimestamp(position, hours);
                  onTimestampChange(timestamp);
                }}
              >
                <div
                  className={`w-3 h-3 rounded-full border-2 border-white shadow-lg transition-transform group-hover:scale-125 ${
                    entry.has_mass_changes
                      ? 'bg-red-500'
                      : entry.change_count > 5
                      ? 'bg-yellow-500'
                      : entry.change_count > 0
                      ? 'bg-blue-500'
                      : 'bg-gray-400'
                  }`}
                />
                {/* Tooltip */}
                <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {entry.change_count} changes<br/>
                  {formatTimestamp(entry.timestamp)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Legend */}
      {timeline.length > 0 && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Events:</h4>
          <div className="space-y-1">
            {timeline.slice(0, 3).map((entry, index) => (
              <div key={index} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      entry.has_mass_changes
                        ? 'bg-red-500'
                        : entry.change_count > 5
                        ? 'bg-yellow-500'
                        : entry.change_count > 0
                        ? 'bg-blue-500'
                        : 'bg-gray-400'
                    }`}
                  />
                  <span className="text-gray-600">
                    {entry.change_count} changes
                  </span>
                </div>
                <span className="text-gray-500">
                  {formatTimestamp(entry.timestamp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Debounce utility
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}