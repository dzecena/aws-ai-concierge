import React from 'react';
import { useChat } from '../../contexts/ChatContext';
import { demoConfig } from '../../config/aws-config';

export const SuggestedQueries: React.FC = () => {
  const { sendMessage, isLoading } = useChat();

  const handleSuggestionClick = async (query: string) => {
    if (isLoading) return;
    
    try {
      await sendMessage(query);
    } catch (error) {
      console.error('Failed to send suggested query:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">
        Try asking me about:
      </h3>
      
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {demoConfig.suggestedQueries.map((query, index) => (
          <button
            key={index}
            onClick={() => handleSuggestionClick(query)}
            disabled={isLoading}
            className="text-left p-4 bg-white border border-gray-200 rounded-lg hover:border-aws-orange hover:shadow-md transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            <div className="flex items-start">
              <div className="flex-shrink-0 w-8 h-8 bg-gray-100 group-hover:bg-aws-orange group-hover:text-white rounded-lg flex items-center justify-center mr-3 transition-colors">
                {index === 0 && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                )}
                {index === 1 && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14-7H3a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2z" />
                  </svg>
                )}
                {index === 2 && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                )}
                {index === 3 && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                )}
                {index === 4 && (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 group-hover:text-aws-orange transition-colors">
                  {query}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
      
      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Or type your own question in the chat box below
        </p>
      </div>
    </div>
  );
};