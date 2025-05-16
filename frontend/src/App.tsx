import React, { useEffect, useState } from 'react';

const API_BASE_URL = 'http://localhost:8000/api'; // your Django API URL

function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/hello/`)  // example endpoint
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(err => console.error('API error:', err));
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Django + React Starter Kit</h1>
      <p>Message from backend: {message || 'Loading...'}</p>
    </div>
  );
}

export default App;
