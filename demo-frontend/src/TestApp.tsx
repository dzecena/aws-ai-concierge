import React, { useState } from 'react';

const TestApp: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [messages, setMessages] = useState<Array<{id: number, type: 'user' | 'ai', content: string}>>([]);
  const [currentMessage, setCurrentMessage] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === 'demo.judge@example.com' && password === 'OqN#ldMRn5TfA@Kw') {
      setIsLoggedIn(true);
    } else {
      alert('Invalid credentials. Use: demo.judge@example.com / OqN#ldMRn5TfA@Kw');
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user' as const,
      content: currentMessage
    };

    setMessages(prev => [...prev, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      let aiResponse = '';
      if (currentMessage.toLowerCase().includes('cost')) {
        aiResponse = '**DEMO DATA** - Your AWS costs this month: $245.67\n\nService Breakdown:\n• EC2: $123.45 (50.2%)\n• RDS: $67.89 (27.6%)\n• S3: $31.23 (12.7%)\n\nPotential Savings: $81.46/month';
      } else if (currentMessage.toLowerCase().includes('security')) {
        aiResponse = '**DEMO DATA** - Security Assessment:\n\n🔴 High Priority: 2 issues\n• SSH access from 0.0.0.0/0\n• Public S3 bucket\n\n🟡 Medium Priority: 3 issues\n• Unencrypted EBS volumes\n• Missing MFA on IAM users';
      } else if (currentMessage.toLowerCase().includes('resource')) {
        aiResponse = '**DEMO DATA** - Resource Inventory:\n\n• EC2 Instances: 12 (8 running, 4 stopped)\n• RDS Databases: 3\n• S3 Buckets: 15 (2.3 TB total)\n• Lambda Functions: 23';
      } else {
        aiResponse = '**DEMO DATA** - I can help you with:\n\n💰 Cost Analysis - "What are my AWS costs?"\n🔍 Resource Discovery - "Show me my EC2 instances"\n🛡️ Security Assessment - "Are there security issues?"\n\nTry asking about costs, security, or resources!';
      }

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai' as const,
        content: aiResponse
      };

      setMessages(prev => [...prev, aiMessage]);
    }, 1000);

    setCurrentMessage('');
  };

  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
          <div className="text-center mb-8">
            <div className="mx-auto h-12 w-12 bg-orange-500 rounded-full flex items-center justify-center mb-4">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">AWS AI Concierge Demo</h1>
            <p className="text-gray-600 mt-2">Sign in to evaluate the AI capabilities</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                placeholder="demo.judge@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                placeholder="OqN#ldMRn5TfA@Kw"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-orange-500 text-white py-2 px-4 rounded-md hover:bg-orange-600 transition-colors"
            >
              Sign In
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-gray-600">
            <p>Demo Credentials:</p>
            <p className="font-mono text-xs mt-1">
              demo.judge@example.com<br />
              OqN#ldMRn5TfA@Kw
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center">
            <div className="h-8 w-8 bg-orange-500 rounded-lg flex items-center justify-center mr-3">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">AWS AI Concierge</h1>
            <span className="ml-2 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">DEMO</span>
          </div>
          <button
            onClick={() => setIsLoggedIn(false)}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 rounded-md hover:bg-gray-100"
          >
            Sign Out
          </button>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 p-6 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <div className="mx-auto h-16 w-16 bg-orange-500 rounded-full flex items-center justify-center mb-6">
                  <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to AWS AI Concierge</h2>
                <p className="text-gray-600 mb-8">Ask me about your AWS infrastructure, costs, security, or resources!</p>
                
                <div className="grid gap-3 max-w-2xl mx-auto">
                  {[
                    "What are my AWS costs this month?",
                    "Show me my EC2 instances",
                    "Are there any security issues?",
                    "Find idle resources"
                  ].map((query, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentMessage(query)}
                      className="text-left p-3 bg-gray-50 border border-gray-200 rounded-lg hover:border-orange-500 hover:bg-orange-50 transition-colors"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-3xl p-4 rounded-lg ${
                      message.type === 'user' 
                        ? 'bg-orange-500 text-white' 
                        : 'bg-gray-100 text-gray-900'
                    }`}>
                      <div className="whitespace-pre-line">{message.content}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSendMessage} className="flex space-x-4">
              <input
                type="text"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                placeholder="Ask me about your AWS infrastructure..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <button
                type="submit"
                disabled={!currentMessage.trim()}
                className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestApp;