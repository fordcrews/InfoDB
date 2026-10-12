import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { login } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { user, loading, setAuthenticated } = useAuth();
  const [email, setEmail] = useState("admin@local.dev");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) {
    return <Navigate to="/" replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const tokenResponse = await login(email, password);
      await setAuthenticated(tokenResponse.access_token);
    } catch {
      setError("Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  }

  function fillDefaults() {
    setEmail("admin@local.dev");
    setPassword("change_me_on_first_login");
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">📡</div>
          <h1>InfoDB</h1>
          <p className="login-subtitle">Network asset inventory &amp; discovery</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              placeholder="admin@local.dev"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
          </div>

          {error && <div className="error">{error}</div>}

          <button
            type="submit"
            className="btn-primary login-btn"
            disabled={submitting || !password}
          >
            {submitting ? "Signing in..." : "Sign in"}
          </button>

          <button
            type="button"
            className="btn-link"
            onClick={fillDefaults}
            style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}
          >
            Use default dev credentials
          </button>
        </form>

        <div className="login-hint">
          Default login: <code>admin@local.dev</code> / check <code>ADMIN_PASSWORD</code> in <code>.env</code>
        </div>
      </div>
    </div>
  );
}