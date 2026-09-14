import React, { useState } from "react";
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react";
import { loginUser, registerUser } from "../services/api";
import PrivacyPolicy from "./PrivacyPolicy";
import TermsAndConditions from "./TermsAndConditions";

function AuthPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem("drugassist_last_email") || "";
    } catch {
      return "";
    }
  });
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
    setConfirmPassword("");
    setShowPassword(false);
    setShowConfirmPassword(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (mode === "register") {
      if (!username.trim()) {
        setError("Please enter a username.");
        return;
      }

      if (!email.trim()) {
        setError("Please enter your email address.");
        return;
      }

      if (password.length < 6) {
        setError("Password must be at least 6 characters.");
        return;
      }

      if (password !== confirmPassword) {
        setError("Passwords do not match.");
        return;
      }
    } else {
      if (!email.trim()) {
        setError("Please enter your email or username.");
        return;
      }
    }

    if (!password) {
      setError("Please enter your password.");
      return;
    }

    try {
      setLoading(true);

      if (mode === "register") {
        const regData = await registerUser(
          username.trim(),
          email.trim(),
          password
        );

        // Seamless auto-login right after registration
        let authData = regData;
        if (!authData?.access_token) {
          authData = await loginUser(
            email.trim(),
            password
          );
        }

        const token =
          authData?.access_token ||
          authData?.token ||
          authData?.jwt;

        if (token) {
          localStorage.setItem(
            "aura_token",
            token
          );
          localStorage.setItem(
            "token",
            token
          );

          if (authData.user) {
            localStorage.setItem(
              "aura_user",
              JSON.stringify(authData.user)
            );
          } else {
            localStorage.setItem(
              "aura_user",
              JSON.stringify({
                email: email.trim(),
                name: username.trim(),
              })
            );
          }

          if (typeof onLogin === "function") {
            onLogin(authData);
          }
          return;
        }

        setSuccess(
          "Account created successfully. You can now log in."
        );

        setMode("login");
        setPassword("");
        setConfirmPassword("");

        return;
      }

      const data = await loginUser(
        email.trim(),
        password
      );

      /*
       * Backend normally returns:
       * {
       *   access_token: "...",
       *   token_type: "bearer",
       *   user: {...}
       * }
       */

      const token =
        data.access_token ||
        data.token ||
        data.jwt;

      if (!token) {
        throw new Error(
          "Login succeeded but no authentication token was returned."
        );
      }

      localStorage.setItem(
        "aura_token",
        token
      );
      localStorage.setItem(
        "token",
        token
      );

      if (data.user) {
        localStorage.setItem(
          "aura_user",
          JSON.stringify(data.user)
        );
      } else {
        localStorage.setItem(
          "aura_user",
          JSON.stringify({
            email: email.trim()
          })
        );
      }

      setPassword("");
      setConfirmPassword("");
      setSuccess("");

      if (typeof onLogin === "function") {
        onLogin(data);
      }

    } catch (err) {
      console.error(
        "AUTHENTICATION ERROR:",
        err
      );

      setError(
        err?.message ||
          "Authentication failed. Please try again."
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">

      <style>{`
        .auth-page {
          width: 100%;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px;
          box-sizing: border-box;
          background: #f7f7f8;
          font-family:
            Inter,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
        }

        .auth-card {
          width: min(430px, 100%);
          background: #ffffff;
          border: 1px solid #e5e5e7;
          border-radius: 18px;
          padding: 34px;
          box-sizing: border-box;
          box-shadow:
            0 12px 40px rgba(0, 0, 0, 0.07);
        }

        .auth-logo {
          width: 52px;
          height: 52px;
          margin: 0 auto 18px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #111111;
          color: #ffffff;
          font-size: 25px;
          font-weight: 700;
        }

        .auth-title {
          margin: 0;
          text-align: center;
          font-size: 28px;
          line-height: 1.2;
          font-weight: 700;
          color: #171717;
        }

        .auth-subtitle {
          margin: 8px 0 28px;
          text-align: center;
          color: #6b6d73;
          font-size: 14px;
          line-height: 1.5;
        }

        .auth-tabs {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 4px;
          padding: 4px;
          margin-bottom: 24px;
          background: #f0f0f2;
          border-radius: 10px;
        }

        .auth-tab {
          border: 0;
          border-radius: 8px;
          padding: 10px;
          background: transparent;
          color: #6b6d73;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
        }

        .auth-tab.active {
          background: #ffffff;
          color: #171717;
          box-shadow:
            0 1px 4px rgba(0, 0, 0, 0.08);
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .auth-field {
          display: flex;
          flex-direction: column;
          gap: 7px;
        }

        .auth-label {
          font-size: 13px;
          font-weight: 600;
          color: #303136;
        }

        .auth-input {
          width: 100%;
          height: 46px;
          padding: 0 13px;
          box-sizing: border-box;
          border: 1px solid #d9d9dd;
          border-radius: 9px;
          outline: none;
          background: #ffffff;
          color: #171717;
          font-size: 14px;
          transition:
            border-color 0.15s ease,
            box-shadow 0.15s ease;
        }

        .auth-input:focus {
          border-color: #999ba1;
          box-shadow:
            0 0 0 3px rgba(0, 0, 0, 0.05);
        }

        .auth-input::placeholder {
          color: #a0a2a8;
        }

        .auth-input-wrapper {
          position: relative;
          width: 100%;
          display: flex;
          align-items: center;
        }

        .auth-input-wrapper .auth-input {
          padding-right: 42px;
        }

        .auth-toggle-pw {
          position: absolute;
          right: 9px;
          top: 50%;
          transform: translateY(-50%);
          background: transparent;
          border: 0;
          padding: 6px;
          color: #71717a;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 6px;
          transition: color 0.15s ease, background-color 0.15s ease;
        }

        .auth-toggle-pw:hover {
          color: #18181b;
          background: #f4f4f5;
        }

        .auth-input.has-error {
          border-color: #ef4444;
        }

        .auth-button {
          width: 100%;
          height: 46px;
          margin-top: 4px;
          border: 0;
          border-radius: 9px;
          background: #171717;
          color: #ffffff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition:
            opacity 0.15s ease,
            transform 0.15s ease;
        }

        .auth-button:hover:not(:disabled) {
          opacity: 0.9;
        }

        .auth-button:active:not(:disabled) {
          transform: translateY(1px);
        }

        .auth-button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .auth-error {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 11px 12px;
          border-radius: 8px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #b91c1c;
          font-size: 13px;
          line-height: 1.4;
        }

        .auth-success {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 11px 12px;
          border-radius: 8px;
          background: #f0fdf4;
          border: 1px solid #bbf7d0;
          color: #15803d;
          font-size: 13px;
          line-height: 1.4;
        }

        .auth-footer {
          margin-top: 22px;
          text-align: center;
          color: #777980;
          font-size: 12px;
          line-height: 1.5;
        }

        @media (max-width: 520px) {
          .auth-page {
            padding: 16px;
          }

          .auth-card {
            padding: 26px 20px;
            border-radius: 14px;
          }

          .auth-title {
            font-size: 25px;
          }
        }
      `}</style>

      <div className="auth-card">

        <div className="auth-logo" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <svg width="34" height="34" viewBox="0 0 24 24" fill="none">
            <rect x="2" y="2" width="20" height="20" rx="4" fill="#0f172a" />
            <path d="M12 6v12" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
            <path d="M6 12h12" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
        </div>

        <h1 className="auth-title">
          DrugAssist
        </h1>

        <p className="auth-subtitle">
          Evidence-first clinical drug intelligence
        </p>

        <div className="auth-tabs">

          <button
            type="button"
            className={
              mode === "login"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode("login")
            }
          >
            Login
          </button>

          <button
            type="button"
            className={
              mode === "register"
                ? "auth-tab active"
                : "auth-tab"
            }
            onClick={() =>
              switchMode("register")
            }
          >
            Register
          </button>

        </div>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
        >

          {mode === "register" && (
            <div className="auth-field">

              <label
                className="auth-label"
                htmlFor="auth-username"
              >
                Username
              </label>

              <input
                id="auth-username"
                className="auth-input"
                type="text"
                value={username}
                onChange={(event) =>
                  setUsername(event.target.value)
                }
                placeholder="Enter your username"
                autoComplete="username"
                disabled={loading}
              />

            </div>
          )}

          <div className="auth-field">

            <label
              className="auth-label"
              htmlFor="auth-email"
            >
              {mode === "login" ? "Email or Username" : "Email"}
            </label>

            <input
              id="auth-email"
              className="auth-input"
              type={mode === "login" ? "text" : "email"}
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder={mode === "login" ? "Enter your email or username" : "Enter your email"}
              autoComplete={mode === "login" ? "username" : "email"}
              disabled={loading}
            />

          </div>

          <div className="auth-field">

            <label
              className="auth-label"
              htmlFor="auth-password"
            >
              Password
            </label>

            <div className="auth-input-wrapper">
              <input
                id="auth-password"
                className={`auth-input ${error && !password ? "has-error" : ""}`}
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                autoComplete={
                  mode === "login"
                    ? "current-password"
                    : "new-password"
                }
                disabled={loading}
              />
              <button
                type="button"
                className="auth-toggle-pw"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex="-1"
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

          </div>

          {mode === "register" && (
            <div className="auth-field">

              <label
                className="auth-label"
                htmlFor="auth-confirm-password"
              >
                Confirm Password
              </label>

              <div className="auth-input-wrapper">
                <input
                  id="auth-confirm-password"
                  className={`auth-input ${error && !confirmPassword ? "has-error" : ""}`}
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(
                      event.target.value
                    )
                  }
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  disabled={loading}
                />
                <button
                  type="button"
                  className="auth-toggle-pw"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                  tabIndex="-1"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

            </div>
          )}

          {error && (
            <div className="auth-error" role="alert" style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                <span>{error}</span>
              </div>
              {mode === "login" && (
                <div style={{ fontSize: "12px", paddingLeft: "24px", opacity: 0.95 }}>
                  Need an account with this email?{" "}
                  <button
                    type="button"
                    onClick={() => switchMode("register")}
                    style={{
                      background: "none",
                      border: "none",
                      padding: 0,
                      color: "#0284c7",
                      cursor: "pointer",
                      fontWeight: 600,
                      textDecoration: "underline",
                      fontFamily: "inherit",
                    }}
                  >
                    Click to Register
                  </button>
                </div>
              )}
            </div>
          )}

          {success && (
            <div className="auth-success" role="status">
              <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
              <span>{success}</span>
            </div>
          )}

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading
              ? mode === "login"
                ? "Logging in..."
                : "Creating account..."
              : mode === "login"
                ? "Login"
                : "Create account"}
          </button>

        </form>

        <div className="auth-footer">
          <p>
            DrugAssist provides reference information from official prescribing documentation and is not a substitute for professional medical advice.
          </p>
          <div style={{ marginTop: "12px", display: "flex", gap: "14px", justifyContent: "center", fontSize: "12px" }}>
            <button
              type="button"
              onClick={() => setShowPrivacy(true)}
              style={{ background: "none", border: "none", color: "#0284c7", cursor: "pointer", textDecoration: "underline", padding: 0 }}
            >
              Privacy Policy
            </button>
            <span style={{ color: "#9ca3af" }}>•</span>
            <button
              type="button"
              onClick={() => setShowTerms(true)}
              style={{ background: "none", border: "none", color: "#0284c7", cursor: "pointer", textDecoration: "underline", padding: 0 }}
            >
              Terms & Conditions
            </button>
          </div>
        </div>

      </div>

      {showPrivacy && <PrivacyPolicy onClose={() => setShowPrivacy(false)} />}
      {showTerms && <TermsAndConditions onClose={() => setShowTerms(false)} />}

    </div>
  );
}

export default AuthPage;