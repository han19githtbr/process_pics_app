import { useEffect, useState } from 'react';
import { ScanSearch, Sparkles } from 'lucide-react';
import { Segmenter } from './components/Segmenter';
import { ImageEnhancer } from './components/ImageEnhancer';
import { Login } from './components/Login/Login';
import { checkSession, logout } from './services/api';
import './styles/globals.css';

function App() {
  // Começa como `false` (tela de login) em vez de `null` (tela de carregamento em branco).
  // A verificação de sessão ocorre em segundo plano: se válida, redireciona silenciosamente
  // para o dashboard sem que o usuário veja nenhuma tela intermediária em branco.
  // Isso elimina o atraso perceptível na abertura do link tanto no desktop quanto no mobile.
  const [authenticated, setAuthenticated] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<'segment' | 'enhance'>('segment');

  useEffect(() => {
    const handleAuthExpired = () => setAuthenticated(false);
    window.addEventListener('auth-expired', handleAuthExpired);
    // Verifica silenciosamente se já existe uma sessão válida.
    // Se sim, redireciona direto para o dashboard; caso contrário, mantém o login visível.
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

  if (!authenticated) return <Login onAuthenticated={() => setAuthenticated(true)} />;

  return (
    <div className="app">
      <nav className="app-top-nav" aria-label="Navegação principal">
        <button
          type="button"
          className={`app-top-nav-btn ${activeView === 'segment' ? 'active' : ''}`}
          onClick={() => setActiveView('segment')}
        >
          <ScanSearch size={15} />
          <span>Segmentador de Letras</span>
        </button>
        <button
          type="button"
          className={`app-top-nav-btn ${activeView === 'enhance' ? 'active' : ''}`}
          onClick={() => setActiveView('enhance')}
        >
          <Sparkles size={15} />
          <span>Melhoria de Qualidade</span>
        </button>
      </nav>

      {activeView === 'segment' ? (
        <Segmenter onLogout={handleLogout} />
      ) : (
        <ImageEnhancer onLogout={handleLogout} />
      )}
    </div>
  );
}

export default App;
