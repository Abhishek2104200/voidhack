import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CheckCircle, AlertTriangle, Loader2, Award } from 'lucide-react';

const ResultsPage = () => {
  const { taskId } = useParams();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8000/v1/status/${taskId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch status');
        }

        const data = await response.json();
        setStatus(data);

        if (data.status === 'COMPLETE' || data.status === 'MANUAL_REVIEW') {
          setLoading(false);
        }
      } catch (err) {
        console.error('Error polling status:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [taskId]);

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="glass-card p-8 text-center">
          <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Error</h2>
          <p className="text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="glass-card p-12 text-center">
          <Loader2 className="w-16 h-16 text-purple-400 mx-auto mb-6 animate-spin" />
          <h2 className="text-2xl font-bold text-white mb-2">Processing Evaluation</h2>
          <p className="text-gray-400 mb-4">
            Status: {status?.step || 'Initializing...'}
          </p>
          <div className="max-w-md mx-auto">
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse" style={{ width: '60%' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const result = status?.result;
  const isComplete = status?.status === 'COMPLETE';

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-4xl font-bold text-white mb-8">Evaluation Results</h1>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="glass-card p-8 text-center">
          <Award className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
          <p className="text-sm text-gray-400 mb-2">Final Grade</p>
          <p className="text-6xl font-bold text-white">{result?.final_grade || 'N/A'}</p>
        </div>

        <div className="glass-card p-8 text-center">
          {isComplete ? (
            <>
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <p className="text-sm text-gray-400 mb-2">Status</p>
              <p className="text-2xl font-bold text-green-400">COMPLETE</p>
            </>
          ) : (
            <>
              <AlertTriangle className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
              <p className="text-sm text-gray-400 mb-2">Status</p>
              <p className="text-2xl font-bold text-yellow-400">MANUAL REVIEW</p>
            </>
          )}
        </div>
      </div>

      <div className="glass-card p-8">
        <div className="flex items-start space-x-4 mb-4">
          <div className="w-1 h-12 bg-gradient-to-b from-blue-500 to-purple-500 rounded-full"></div>
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Grader's Justification</h2>
            <p className="text-gray-400 leading-relaxed">
              {result?.justification || 'No justification available.'}
            </p>
          </div>
        </div>
      </div>

      <div className="glass-card p-8">
        <div className="flex items-start space-x-4 mb-4">
          <div className="w-1 h-12 bg-gradient-to-b from-purple-500 to-pink-500 rounded-full"></div>
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Feedback for Student</h2>
            <p className="text-gray-400 leading-relaxed">
              {result?.feedback || 'No feedback available.'}
            </p>
          </div>
        </div>
      </div>

      <div className="glass-card p-6 bg-white/5">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">Task ID:</span>
          <span className="text-gray-300 font-mono">{taskId}</span>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
