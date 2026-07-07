import React, { useState, useEffect } from 'react';
import api from '../../services/api';

interface TestSummaryProps {
  protocol: string;
  projectId?: string | null;
}

interface SummaryItem {
  test_name: string;
  count: number;
}

const TestSummary: React.FC<TestSummaryProps> = ({ protocol, projectId }) => {
  const [summary, setSummary] = useState<SummaryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, [protocol, projectId]);

  const loadSummary = async () => {
    setIsLoading(true);
    try {
      // Pass projectId as query parameter
      const response = await api.get(`/get-${protocol.toLowerCase()}-summary`, {
        params: { projectId }
      });
      if (response.data) {
        setSummary(response.data);
      }
    } catch (error) {
      console.error('Error loading summary:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Summary</h3>
        <div className="flex justify-center py-8">
          <div className="w-6 h-6 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Test Summary</h3>
      {summary.length === 0 ? (
        <p className="text-sm text-gray-500 text-center py-4">No tests available</p>
      ) : (
        <div className="space-y-2">
          {summary.map((item, index) => (
            <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <span className="text-sm text-gray-600">{item.test_name}</span>
              <span className="text-sm font-semibold text-gray-800">{item.count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TestSummary;