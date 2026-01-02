import { useState } from 'react';
import { useProfile } from './hooks/useProfile';
import InterviewPrep from './components/InterviewPrep';

function App() {
  const { profile, loading, error } = useProfile();
  const [activeTab, setActiveTab] = useState('interview');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-neutral-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="card max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Profile</h2>
          <p className="text-neutral-600">{error}</p>
          <p className="text-sm text-neutral-500 mt-4">
            Make sure documents have been processed in ~/Downloads
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-white">
      {/* Sidebar */}
      <aside className="w-64 border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-lg font-semibold text-gray-900">Interview Prep</h1>
          <p className="text-xs text-gray-500 mt-1">{profile?.personal_info?.name || 'Your Profile'}</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <div
            onClick={() => setActiveTab('interview')}
            className={activeTab === 'interview' ? 'sidebar-link-active' : 'sidebar-link'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <span>Interview Practice</span>
          </div>

          <div
            onClick={() => setActiveTab('profile')}
            className={activeTab === 'profile' ? 'sidebar-link-active' : 'sidebar-link'}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <span>Profile</span>
          </div>
        </nav>

        <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
          Auto-refreshes every 30s
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto px-8 py-12">
        {activeTab === 'profile' && (
          <div className="space-y-6">
            {/* Profile Summary */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Profile</h2>
              <div className="card">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Name</p>
                    <p className="text-sm font-medium text-gray-900">{profile?.personal_info?.name || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Email</p>
                    <p className="text-sm font-medium text-gray-900">{profile?.personal_info?.email || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Location</p>
                    <p className="text-sm font-medium text-gray-900">{profile?.personal_info?.location || 'Not set'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Work Experiences</p>
                    <p className="text-sm font-medium text-gray-900">{profile?.work_experience?.length || 0}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Work Experience */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Work Experience</h2>
              <div className="space-y-6">
                {profile?.work_experience?.map((exp, idx) => (
                  <div key={idx} className="card">
                    <h3 className="font-semibold text-base text-gray-900">{exp.role}</h3>
                    <p className="text-sm text-gray-600 mt-1">{exp.company}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {exp.start_date} - {exp.is_current ? 'Present' : exp.end_date}
                    </p>
                    {exp.responsibilities && exp.responsibilities.length > 0 && (
                      <ul className="mt-3 space-y-1.5">
                        {exp.responsibilities.slice(0, 3).map((resp, i) => (
                          <li key={i} className="text-sm text-gray-700 leading-relaxed">• {resp}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Skills */}
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6">Skills</h2>
              <div className="card">
                <div className="flex flex-wrap gap-2">
                  {profile?.skills?.technical?.programming_languages?.map((skill, idx) => (
                    <span key={idx} className="badge-primary">{skill}</span>
                  ))}
                  {profile?.skills?.technical?.frameworks?.map((skill, idx) => (
                    <span key={idx} className="badge-accent">{skill}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'interview' && (
          <InterviewPrep profile={profile} />
        )}
        </div>
      </main>
    </div>
  );
}

export default App;
