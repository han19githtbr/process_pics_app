import { useEffect, useState } from 'react';
import { Segmenter } from './components/Segmenter';
import { Login } from './components/Login/Login';
import { checkSession, logout } from './services/api';
import './styles/globals.css';

function App() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    const handleAuthExpired = () => setAuthenticated(false);
    window.addEventListener('auth-expired', handleAuthExpired);
    checkSession().then(setAuthenticated).catch(() => setAuthenticated(false));

    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Mesmo que a chamada falhe (ex.: sessão já expirada no backend),
      // o usuário é redirecionado para a tela de login localmente.
    } finally {
      setAuthenticated(false);
    }
  };

  if (authenticated === null) return <div className="app app-loading" aria-label="Carregando aplicação" />;
  if (!authenticated) return <Login onAuthenticated={() => setAuthenticated(true)} />;

  return (
    <div className="app">
      <Segmenter onLogout={handleLogout} />
    </div>
  );
}

export default App;
