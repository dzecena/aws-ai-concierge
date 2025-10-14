import React from 'react'
import ReactDOM from 'react-dom/client'
import TestApp from './TestApp'
import './index.css'

// Use TestApp for simple authentication demo
// Avoiding import of App to prevent Amplify initialization issues

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TestApp />
  </React.StrictMode>,
)