import { useState } from 'react';
import interviewService from '../services/interviewService';

export default function InterviewPrep({ profile }) {
  const [question, setQuestion] = useState('');
  const [selectedJob, setSelectedJob] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await interviewService.generateResponse(
        question,
        profile,
        selectedJob || null
      );
      setResponse(result);
    } catch (err) {
      setError('Failed to generate response. Make sure the API server is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (response?.response) {
      navigator.clipboard.writeText(response.response);
      alert('Response copied to clipboard!');
    }
  };

  const exampleQuestions = [
    "Tell me about a time you led a project",
    "Describe a challenging technical problem you solved",
    "How do you handle disagreements with team members?",
    "What's your greatest professional achievement?"
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Interview Practice</h2>

        {/* Job Selector */}
        {profile?.job_applications && profile.job_applications.length > 0 && (
          <div className="mb-6">
            <label className="block text-xs text-gray-500 mb-2">
              Job Context (Optional)
            </label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-gray-400 transition-all duration-200"
            >
              <option value="">Select a job application...</option>
              {profile.job_applications.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.position} at {job.company}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Question Input */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs text-gray-500 mb-2">
              Interview Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter an interview question..."
              className="w-full border border-gray-300 rounded-md px-3 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-gray-400 transition-all duration-200 resize-none"
              rows={4}
            />
          </div>

          <div>
            <p className="text-xs text-gray-500 mb-2">Example questions:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(q)}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded transition-all duration-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!question.trim() || loading}
            className="btn-primary w-full"
          >
            {loading ? 'Generating...' : 'Generate Response'}
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="card text-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-600">Analyzing your profile and crafting response...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card border-red-200 bg-red-50">
          <p className="text-sm text-red-900">{error}</p>
          <p className="text-xs text-red-700 mt-2">
            Start the API server: <code className="bg-red-100 px-2 py-1 rounded text-xs">cd api && python server.py</code>
          </p>
        </div>
      )}

      {/* Response Display */}
      {response && !loading && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Your Response</h3>
            <button onClick={handleCopy} className="btn-secondary text-sm">
              Copy
            </button>
          </div>

          <div className="card bg-gray-50">
            <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
              {response.response}
            </p>
          </div>

          {response.job_context && (
            <div className="card border-gray-300">
              <p className="text-xs text-gray-600">
                <strong className="text-gray-900">Tailored for:</strong> {response.job_context.position} at {response.job_context.company}
              </p>
            </div>
          )}

          {response.relevant_experiences && response.relevant_experiences.length > 0 && (
            <div className="card">
              <p className="text-xs font-medium text-gray-900 mb-2">Referenced Experiences</p>
              <ul className="text-xs text-gray-600 space-y-1">
                {response.relevant_experiences.map((exp, idx) => (
                  <li key={idx}>• {exp}</li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={() => setResponse(null)}
            className="btn-secondary w-full"
          >
            Generate New Response
          </button>
        </div>
      )}

      {/* Empty State */}
      {!response && !loading && !error && (
        <div className="card text-center py-16 bg-gray-50">
          <h3 className="text-base font-semibold text-gray-900 mb-2">Ready to Practice?</h3>
          <p className="text-sm text-gray-600 mb-6 max-w-md mx-auto">
            Enter an interview question above and I'll craft an authentic response using your actual experiences.
          </p>
          <div className="flex justify-center gap-2">
            <span className="badge-primary">AI-Powered</span>
            <span className="badge-accent">Your Experiences</span>
            <span className="badge-primary">STAR Method</span>
          </div>
        </div>
      )}
    </div>
  );
}
