import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export const WelcomePanel: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="text-center py-8">
      <div className="mx-auto h-16 w-16 bg-gradient-to-br from-aws-orange to-orange-600 rounded-full flex items-center justify-center mb-6">
        <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>
      
      <h2 className="text-2xl font-bold text-gray-900 mb-2">
        Welcome to AWS AI Concierge
      </h2>
      
      <p className="text-lg text-gray-600 mb-6 max-w-2xl mx-auto">
        Hello {user?.name || 'Judge'}! I'm your AI assistant for AWS infrastructure management. 
        I can help you analyze costs, discover resources, assess security, and optimize your AWS environment.
      </p>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-3xl mx-auto">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">What I Can Help You With</h3>
        
        <div className="grid md:grid-cols-2 gap-4 text-left">
          <div className="space-y-3">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Cost Analysis</h4>
                <p className="text-sm text-gray-600">Analyze spending, identify savings opportunities, and optimize costs</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14-7H3a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Resource Discovery</h4>
                <p className="text-sm text-gray-600">Inventory and monitor your AWS resources across all regions</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Security Assessment</h4>
                <p className="text-sm text-gray-600">Identify security issues and compliance violations</p>
              </div>
            </div>
            
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h4 className="font-medium text-gray-900">Optimization</h4>
                <p className="text-sm text-gray-600">Find idle resources and performance improvement opportunities</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg max-w-2xl mx-auto">
        <div className="flex items-center justify-center mb-2">
          <svg className="w-5 h-5 text-yellow-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm font-medium text-yellow-800">Demo Environment</span>
        </div>
        <p className="text-sm text-yellow-700">
          This is a demonstration environment. All data shown is simulated for evaluation purposes and does not reflect real AWS resources.
        </p>
      </div>
    </div>
  );
};