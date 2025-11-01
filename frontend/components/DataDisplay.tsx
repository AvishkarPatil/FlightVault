'use client';

import { useState, useEffect } from 'react';
import { Database, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';
import { FlightVaultAPI } from '@/lib/api';
import { Airport } from '@/types';

interface DataDisplayProps {
  table: string;
  timestamp: string;
}

type TableRecord = Airport | any; // Generic type for different table records

export default function DataDisplay({ table, timestamp }: DataDisplayProps) {
  const [data, setData] = useState<TableRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [limit] = useState(25);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const response = await FlightVaultAPI.getState(
          table,
          timestamp,
          limit,
          currentPage * limit
        ) as { records: TableRecord[]; total_count: number };
        setData(response.records || []);
        setTotalCount(response.total_count || 0);
      } catch (error) {
        console.error('Failed to load data:', error);
        setData([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [table, timestamp, currentPage, limit]);

  const totalPages = Math.ceil(totalCount / limit);
  const [isHistorical, setIsHistorical] = useState(false);
  
  useEffect(() => {
    setIsHistorical(new Date(timestamp) < new Date(Date.now() - 60000));
  }, [timestamp]);

  const handleExport = () => {
    const headers = table === 'airports' 
      ? ['ID', 'Name', 'City', 'Country', 'IATA', 'ICAO']
      : ['ID', 'Name', 'Country', 'Active'];
    
    const rows = data.map(row => {
      if (table === 'airports') {
        return [
          row.airport_id || row.id,
          `"${row.name || ''}"`,
          `"${row.city || ''}"`,
          `"${row.country || ''}"`,
          row.iata_code || '',
          row.icao_code || ''
        ].join(',');
      } else {
        return [
          row.airline_id || row.route_id || row.id,
          `"${row.name || ''}"`,
          `"${row.country || ''}"`,
          row.active || ''
        ].join(',');
      }
    });
    
    const csv = [headers.join(','), ...rows].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${table}_${timestamp.split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Database className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900 capitalize">
              {table} Data
            </h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>{formatTimestamp(timestamp)}</span>
              {isHistorical && (
                <span className="px-2 py-1 bg-warning-100 text-warning-700 rounded text-xs font-medium">
                  Historical
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">
            {totalCount.toLocaleString()} records
          </span>
          <button
            onClick={handleExport}
            disabled={data.length === 0}
            className="btn-secondary flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Data Table */}
      {!loading && data.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-medium text-gray-700">ID</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Name</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">City</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Country</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">IATA</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">ICAO</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-700">Coordinates</th>
                </tr>
              </thead>
              <tbody>
                {data.map((row: any, index) => {
                  const rowId = row.airport_id || row.airline_id || row.route_id || row.id || index;
                  return (
                    <tr
                      key={rowId}
                      className={`border-b border-gray-100 hover:bg-gray-50 ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                      }`}
                    >
                      <td className="py-3 px-4 text-sm font-mono text-gray-600">
                        {rowId}
                      </td>
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        {row.name || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {row.city || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {row.country || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm font-mono text-gray-600">
                        {row.iata_code || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm font-mono text-gray-600">
                        {row.icao_code || '-'}
                      </td>
                      <td className="py-3 px-4 text-sm font-mono text-gray-600">
                        {row.latitude && row.longitude ? `${row.latitude.toFixed(2)}, ${row.longitude.toFixed(2)}` : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                Showing {currentPage * limit + 1} to {Math.min((currentPage + 1) * limit, totalCount)} of {totalCount.toLocaleString()} records
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0}
                  className="btn-secondary flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>
                
                <span className="text-sm text-gray-600">
                  Page {currentPage + 1} of {totalPages}
                </span>
                
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                  disabled={currentPage >= totalPages - 1}
                  className="btn-secondary flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>Next</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!loading && data.length === 0 && (
        <div className="text-center py-12">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Found</h3>
          <p className="text-gray-500">
            No records found for the selected timestamp.
          </p>
        </div>
      )}
    </div>
  );
}