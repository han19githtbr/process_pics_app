import { FormEvent, useState } from 'react';
import { Eye, EyeOff, LockKeyhole, LogIn, ScanSearch } from 'lucide-react';
import { checkSession, login } from '../../services/api';
import './Login.css';

type LoginProps = { onAuthenticated: () => void };

export const Login = ({ onAuthenticated }: LoginProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedEmail = email.trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) {
      setError('Digite um endereço de e-mail válido.');
      return;
    }
    if (!password) {
      setError('Digite sua senha.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(normalizedEmail, password);
      if (!(await checkSession())) {
        throw new Error('A sessão não foi persistida pelo navegador.');
      }
      onAuthenticated();
    } catch (requestError: any) {
      setError(
        requestError?.response?.data?.detail ||
          requestError?.message ||
          'Não foi possível iniciar a sessão.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="login-shell">
      <div className="login-orbit login-orbit-one" />
      <div className="login-orbit login-orbit-two" />
      <section className="login-layout">
        <div className="login-intro">
          <div className="login-brand-mark"><ScanSearch size={25} strokeWidth={2.2} /></div>
          <p className="login-kicker">Pattern Checker <span>/</span> Vision Studio</p>
          <h1>Precisão em cada<br /><em>fragmento.</em></h1>
          <p className="login-description">Um espaço privado para transformar imagens em dados visuais claros, rastreáveis e prontos para análise.</p>
          <div className="login-signal"><span /> Ambiente protegido <strong>·</strong> acesso administrativo</div>
        </div>

        <div className="login-panel">
          <div className="login-panel-heading">
            <div className="login-icon"><LockKeyhole size={19} /></div>
            <div><p>Área restrita</p><h2>Entrar no Studio</h2></div>
          </div>
          <form onSubmit={handleSubmit} noValidate>
            <label htmlFor="email">E-mail</label>
            <input id="email" type="email" autoComplete="username" value={email} onChange={event => setEmail(event.target.value)} placeholder="seu@email.com" aria-invalid={Boolean(error)} />
            <label htmlFor="password">Senha</label>
            <div className="password-field">
              <input id="password" type={showPassword ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} placeholder="Digite sua senha" aria-invalid={Boolean(error)} />
              <button type="button" className="password-toggle" onClick={() => setShowPassword(current => !current)} aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            {error && <p className="login-error" role="alert">{error}</p>}
            <button className="login-submit" type="submit" disabled={loading}>
              {loading ? 'Verificando...' : <><span>Acessar plataforma</span><LogIn size={18} /></>}
            </button>
          </form>
          <p className="login-footnote">Acesso exclusivo do administrador</p>
        </div>
      </section>
    </main>
  );
};
