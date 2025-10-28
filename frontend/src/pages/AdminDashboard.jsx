import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Users, FileCheck, Award } from 'lucide-react';

const classAveragesData = [
  { class: 'CS-101', average: 78 },
  { class: 'CS-102', average: 82 },
  { class: 'CS-201', average: 75 },
  { class: 'CS-202', average: 88 },
  { class: 'CS-301', average: 85 },
];

const gradeDistributionData = [
  { name: 'A (90-100)', value: 25, color: '#10b981' },
  { name: 'B (80-89)', value: 35, color: '#3b82f6' },
  { name: 'C (70-79)', value: 20, color: '#f59e0b' },
  { name: 'D (60-69)', value: 12, color: '#ef4444' },
  { name: 'F (0-59)', value: 8, color: '#7c3aed' },
];

const recentSubmissions = [
  { taskId: 'a7b3c9d1', examId: 'CS-101', grade: 85, status: 'COMPLETE' },
  { taskId: 'e4f2g8h5', examId: 'CS-202', grade: 92, status: 'COMPLETE' },
  { taskId: 'i1j6k3l9', examId: 'CS-301', grade: 78, status: 'MANUAL_REVIEW' },
  { taskId: 'm2n7o4p8', examId: 'CS-101', grade: 88, status: 'COMPLETE' },
  { taskId: 'q5r1s6t2', examId: 'CS-201', grade: 73, status: 'COMPLETE' },
];

const highestAverages = [
  { name: 'Advanced Algorithms', average: 92 },
  { name: 'Database Systems', average: 88 },
  { name: 'Data Structures', average: 85 },
  { name: 'Operating Systems', average: 82 },
];

const AdminDashboard = () => {
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <h1 className="text-4xl font-bold text-white mb-8">Admin Dashboard</h1>

      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Total Submissions</p>
              <p className="text-3xl font-bold text-white">1,247</p>
            </div>
            <FileCheck className="w-10 h-10 text-blue-400" />
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Active Students</p>
              <p className="text-3xl font-bold text-white">342</p>
            </div>
            <Users className="w-10 h-10 text-green-400" />
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Avg. Grade</p>
              <p className="text-3xl font-bold text-white">82%</p>
            </div>
            <Award className="w-10 h-10 text-yellow-400" />
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400 mb-1">Pass Rate</p>
              <p className="text-3xl font-bold text-white">87%</p>
            </div>
            <TrendingUp className="w-10 h-10 text-purple-400" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="glass-card p-6">
          <h2 className="text-xl font-bold text-white mb-6">Class Averages</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={classAveragesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ffffff20" />
              <XAxis dataKey="class" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="average" fill="url(#colorGradient)" radius={[8, 8, 0, 0]} />
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card p-6">
          <h2 className="text-xl font-bold text-white mb-6">Grade Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={gradeDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {gradeDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-6">Recent Submissions</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">Task ID</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">Exam ID</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">Grade</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-300">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentSubmissions.map((submission) => (
                <tr key={submission.taskId} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="py-3 px-4 text-gray-400 font-mono text-sm">{submission.taskId}</td>
                  <td className="py-3 px-4 text-gray-300">{submission.examId}</td>
                  <td className="py-3 px-4 text-white font-semibold">{submission.grade}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        submission.status === 'COMPLETE'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}
                    >
                      {submission.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-6">Highest Averages</h2>
        <div className="space-y-4">
          {highestAverages.map((course, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-bold text-sm">
                  {index + 1}
                </div>
                <span className="text-gray-300">{course.name}</span>
              </div>
              <span className="text-2xl font-bold text-white">{course.average}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
