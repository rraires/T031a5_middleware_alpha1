import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Enable React strict mode for development
const StrictMode = React.StrictMode

// Get the root element
const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found. Make sure you have a div with id="root" in your HTML.')
}

// Create root and render the app
const root = ReactDOM.createRoot(rootElement)

root.render(
  <StrictMode>
    <App />
  </StrictMode>
)

// Hot Module Replacement (HMR) for development
if (import.meta.hot) {
  import.meta.hot.accept()
}