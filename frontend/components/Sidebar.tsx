'use client';

import { useState } from 'react';
import { Clock, Database, GitCompare, Settings, RotateCcw, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  { id: 'timeline', label: 'Timeline Explorer', icon: Clock },
  { id: 'data', label: 'Data Browser', icon: Database },
  { id: 'compare', label: 'Compare States', icon: GitCompare },
  { id: 'restore', label: 'Recovery Center', icon: RotateCcw },
  { id: 'activity', label: 'Activity Log', icon: Activity },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  return (
    <div className="w-64 bg-white border-r border-gray-200 h-screen">
      <div className="p-6">
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">FlightVault</h1>
            <p className="text-xs text-gray-500">Time-Travel Database</p>
          </div>
        </div>

        <nav className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={cn(
                  'w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors',
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700 border border-primary-200'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="text-sm font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
}