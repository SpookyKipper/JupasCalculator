import { useEffect } from "react";
import { useLang } from "../lib/i18n";
import { useTheme } from "../lib/theme";
import { AppHeader } from "./AppHeader";
import "./AboutPage.css";


type Props = {
  onClose: () => void;
};

export function AboutPage({ onClose }: Props) {
  const { t } = useLang();
  const [theme, setTheme] = useTheme();

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <main className="app-shell layout-mobile about-view about-cover" role="dialog" aria-modal="true" aria-labelledby="about-title">
      <AppHeader theme={theme} onThemeChange={setTheme} onBack={onClose} onBrandClick={onClose} hideAboutLink />

      <article className="about-doc">
        <header className="about-hero">
          <p className="eyebrow">{t("about.eyebrow")}</p>
          <h1 className="about-title" id="about-title">
            JUPASCal <span className="about-title-year">2027</span>
          </h1>
          <p className="about-lede">{t("about.lede")}</p>
          <p className="about-free">{t("about.free")}</p>
        </header>

        <ul className="about-facts">
          <li>
            <strong>10</strong>
            <span>{t("about.facts.institutions")}</span>
          </li>
          <li>
            <strong>{__PROGRAMME_COUNT__}</strong>
            <span>{t("about.facts.programmes")}</span>
          </li>
          <li>
            <strong>2026</strong>
            <span>{t("about.facts.baselines")}</span>
          </li>
        </ul>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v18h18" />
              <path d="M7 14l3-4 3 3 4-6" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.scores.h")}</h2>
            <p>{t("about.scores.p")}</p>
          </div>
        </section>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <ellipse cx="12" cy="5" rx="8" ry="3" />
              <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
              <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.more.h")}</h2>
            <p>{t("about.more.p")}</p>
          </div>
        </section>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3 4 7v6c0 4.4 3.4 7.4 8 8 4.6-.6 8-3.6 8-8V7l-8-4z" />
              <path d="M12 8v5" />
              <path d="M12 16.5h.01" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.ai.h")}</h2>
            <p>{t("about.ai.p")}</p>
          </div>
        </section>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v5" />
              <path d="M12 16.5h.01" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.disclaimer.h")}</h2>
            <p>{t("about.disclaimer.p")}</p>
          </div>
        </section>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <rect x="5" y="11" width="14" height="10" rx="2" />
              <path d="M8 11V7a4 4 0 0 1 8 0v4" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.privacy.h")}</h2>
            <p>{t("about.privacy.p")}</p>
          </div>
        </section>

        <section className="about-card">
          <span className="about-card-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
            </svg>
          </span>
          <div className="about-card-text">
            <h2>{t("about.source.h")}</h2>
            <p>{t("about.source.p.pre")}</p>
            <div className="about-source-actions">
              <a
                className="about-source-btn"
                href="https://jupascal.com/"
                target="_blank"
                rel="noreferrer"
              >
                {t("about.source.original")}
              </a>
              <a
                className="about-source-btn is-secondary"
                href="https://www.jupas.edu.hk/"
                target="_blank"
                rel="noreferrer"
              >
                {t("about.source.jupas")}
              </a>
            </div>
          </div>
        </section>

        <footer className="about-version">
          <span>
            {__APP_VERSION__.includes("-beta") ? <><strong>{t("about.beta")}</strong> · </> : null}
            {t("about.version")} <code>{__APP_VERSION__}</code>
            {__ADMISSION_CYCLE__ ? <> · {t("about.cycle", { year: __ADMISSION_CYCLE__ })}</> : null}
            {" · "}{t("about.build")} <code>{__BUILD_SHA__}</code> ({__BUILD_DATE__})
          </span>
        </footer>
      </article>
    </main>
  );
}
