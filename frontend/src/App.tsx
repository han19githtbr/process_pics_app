import { useEffect, useState } from 'react';
import { Segmenter } from './components/Segmenter';
import { Login } from './components/Login/Login';
import { checkSession } from './services/api';
import './styles/globals.css';

function App() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const handleAuthExpired = () => setAuthenticated(false);
    window.addEventListener('auth-expired', handleAuthExpired);
    checkSession().then(setAuthenticated).catch(() => setAuthenticated(false));

    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, []);

  if (authenticated === null) return <div className="app app-loading" aria-label="Carregando aplicação" />;
  if (!authenticated) return <Login onAuthenticated={() => setAuthenticated(true)} />;

  return (
    <div className="app">
      <Segmenter />
    </div>
  );
}

export default App;
