"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowRight, Activity, Shield, Zap, Check } from "lucide-react";
import { motion, useInView } from "framer-motion";
import styles from "./LandingPage.module.css";

// Reusable Reveal Component
function Reveal({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-10%" });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 28 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 28 }}
      transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// CountUp Component
function CountUp({ target, duration = 1.4, decimals = 0, prefix = "", suffix = "", className = "" }: { target: number, duration?: number, decimals?: number, prefix?: string, suffix?: string, className?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-10%" });
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    let start = 0;
    const end = target;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = (currentTime - startTime) / 1000;
      const progress = Math.min(elapsed / duration, 1);
      
      // ease-out cubic
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      
      setValue(start + (end - start) * easeProgress);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    requestAnimationFrame(animate);
  }, [isInView, target, duration]);

  return <div ref={ref} className={className}>{prefix}{value.toFixed(decimals)}{suffix}</div>;
}

export function LandingPage() {
  const [scrolled, setScrolled] = useState(false);
  const [mockupTransform, setMockupTransform] = useState({ px: 0, py: 0 });

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 24);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const px = (e.clientX / window.innerWidth - 0.5) * 2;
      const py = (e.clientY / window.innerHeight - 0.5) * 2;
      setMockupTransform({ px, py });
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const CardHoverEffect = ({ children, className = "" }: { children: React.ReactNode, className?: string }) => {
    const cardRef = useRef<HTMLDivElement>(null);
    const handleMouseMove = (e: React.MouseEvent) => {
      if (!cardRef.current) return;
      const rect = cardRef.current.getBoundingClientRect();
      cardRef.current.style.setProperty("--mx", `${e.clientX - rect.left}px`);
      cardRef.current.style.setProperty("--my", `${e.clientY - rect.top}px`);
    };
    return (
      <div ref={cardRef} className={`${styles.card} ${className}`} onMouseMove={handleMouseMove}>
        {children}
      </div>
    );
  };

  return (
    <div className={styles.landingContainer}>
      <div className={`${styles.glow} ${styles.glowG1}`}></div>
      <div className={`${styles.glow} ${styles.glowG2}`}></div>
      <div className={`${styles.glow} ${styles.glowG3}`}></div>

      {/* NAV */}
      <nav className={`${styles.nav} ${scrolled ? styles.navScrolled : ""}`}>
        <div className={`${styles.container} ${styles.navInner}`}>
          <Link className={styles.logo} href="#">
            <span className={styles.logoMark}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 0 0 3 3 3 3 0 0 0 3-3 3 3 0 0 0-3-3H6a3 3 0 0 0-3 3 3 3 0 0 0 3 3 3 3 0 0 0 3-3V6a3 3 0 0 0-3-3 3 3 0 0 0-3 3 3 3 0 0 0 3 3h12a3 3 0 0 0 3-3 3 3 0 0 0-3-3Z" />
              </svg>
            </span>
            <span className={`${styles.logoText} ${styles.devanagariText}`}>प्रतिक्रिया</span>
            <span className={styles.logoText}>PRATIKRIYA</span>
          </Link>
          <div className={styles.navLinks}>
            <a className={styles.ulink} href="#top">Home</a>
            <a className={styles.ulink} href="#features">Capabilities</a>
            <a className={styles.ulink} href="#benchmarks">Performance</a>
          </div>
          <Link href="/dashboard" className={styles.ctaPill}>
            Access Terminal <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* HERO */}
      <header id="top" className={`${styles.container} ${styles.hero}`}>
        <div>
          <Reveal>
            <div className={styles.tagRow}>
              <span className={styles.dot}></span>
              <span className={styles.monoLabel}>Secure Enclave Active</span>
            </div>
          </Reveal>
          <Reveal delay={0.1}>
            <h1>Engineered for<br /><em className={styles.serif}>precision</em> forensics.</h1>
          </Reveal>
          <Reveal delay={0.2}>
            <p className={styles.heroLead}>
              PRATIKRIYA is a next-generation DFIR platform that pairs editorial restraint with surgical analysis — high-speed ingestion, automated threat hunting, and a zero-trust core, built for air-gapped investigations.
            </p>
          </Reveal>
          <Reveal delay={0.3}>
            <div className={styles.btnRow}>
              <Link href="/dashboard" className={`${styles.btn} ${styles.btnSolid}`}>
                Initialize Case <ArrowRight size={14} />
              </Link>
              <a href="#features" className={`${styles.btn} ${styles.btnGhost}`}>
                System Specs
              </a>
            </div>
          </Reveal>
        </div>
        
        <Reveal delay={0.4}>
          <div className={styles.mockup}>
            <div className={`${styles.glassCard} ${styles.mcMain}`} style={{ transform: `rotate(-3deg) translate(${mockupTransform.px * 12 * 0.4}px, ${mockupTransform.py * 12 * 0.4}px)` }}>
              <div className={styles.monoLabel}>Live Ingestion Throughput</div>
              <div className={styles.bars}>
                {[42, 68, 55, 82, 60, 90, 48, 72].map((h, i) => (
                  <div key={i} className={styles.bar} style={{ height: `${h}%`, animationDelay: `${i * 0.18}s` }}></div>
                ))}
              </div>
              <div className={styles.spark}>
                <i className={styles.on}></i><i></i><i className={styles.on}></i><i></i><i className={styles.on}></i><i></i>
              </div>
            </div>
            <div className={`${styles.glassCard} ${styles.mcBadge}`} style={{ transform: `rotate(4deg) translate(${mockupTransform.px * 12 * 1}px, ${mockupTransform.py * 12 * 1}px)` }}>
              <div className={styles.monoLabel}>Detection Latency</div>
              <div className={styles.kv}>
                <span className={styles.monoLabel}>p50</span><span className={`${styles.v} ${styles.em}`}>0.2ms</span>
              </div>
              <div className={styles.kv}>
                <span className={styles.monoLabel}>p99</span><span className={styles.v}>0.8ms</span>
              </div>
            </div>
            <div className={`${styles.glassCard} ${styles.mcMini}`} style={{ transform: `rotate(2deg) translate(${mockupTransform.px * 12 * 0.7}px, ${mockupTransform.py * 12 * 0.7}px)` }}>
              <div className={styles.monoLabel}>Threat Feed</div>
              <div className={styles.kv}>
                <span className={styles.monoLabel}>IOCs</span><span className={`${styles.v} ${styles.em}`}>12M+</span>
              </div>
              <div className={styles.kv}>
                <span className={styles.monoLabel}>Updates</span><span className={styles.v}>Live</span>
              </div>
            </div>
          </div>
        </Reveal>
      </header>

      {/* FEATURES */}
      <section id="features" className={`${styles.container} ${styles.sec}`}>
        <Reveal className={styles.secHead}>
          <span className={styles.monoLabel}>/ 01 — Capabilities</span>
          <h2>A platform built<br />around <em className={styles.serif}>evidence</em>.</h2>
          <p>
            Every layer is tuned for the moments that matter in an investigation. No noise, no bloat — only the precision required to process artifacts at scale.
          </p>
        </Reveal>
        <div className={styles.grid3}>
          <Reveal delay={0.1}>
            <CardHoverEffect>
              <span className={styles.num}>01</span>
              <div className={styles.iconBox}>
                <Zap size={24} />
              </div>
              <h3>Real-time Ingestion</h3>
              <p>
                Artifacts process in sub-millisecond windows through a highly optimized data pipeline and hardware-accelerated hashing.
              </p>
            </CardHoverEffect>
          </Reveal>
          <Reveal delay={0.2}>
            <CardHoverEffect>
              <span className={styles.num}>02</span>
              <div className={styles.iconBox}>
                <Activity size={24} />
              </div>
              <h3>Deep Analysis</h3>
              <p>
                Advanced heuristics and signature matching automatically surface threat actors, lateral movement, and persistence mechanisms.
              </p>
            </CardHoverEffect>
          </Reveal>
          <Reveal delay={0.3}>
            <CardHoverEffect>
              <span className={styles.num}>03</span>
              <div className={styles.iconBox}>
                <Shield size={24} />
              </div>
              <h3>Chain of Custody</h3>
              <p>
                Every action is cryptographically logged and BSA certified, maintaining absolute integrity for legal proceedings.
              </p>
            </CardHoverEffect>
          </Reveal>
        </div>
      </section>

      {/* BENCHMARKS */}
      <section id="benchmarks" className={`${styles.container} ${styles.sec}`}>
        <Reveal className={styles.secHead}>
          <span className={styles.monoLabel}>/ 02 — Performance</span>
          <h2>The numbers,<br />without the <em className={styles.serif}>theatre</em>.</h2>
          <p>
            Measured against legacy forensic toolkits on identical workloads. Built for speed when every second of an incident matters.
          </p>
        </Reveal>
        <div className={styles.table}>
          <div className={`${styles.trow} ${styles.thead}`}>
            <span>Metric</span><span>PRATIKRIYA</span><span>Legacy</span><span className={styles.colGain}>Gain</span><span className={styles.colCheck}></span>
          </div>
          <Reveal delay={0.1} className={styles.trow}>
            <div className={styles.tmetric}>File Parsing (p50)</div>
            <CountUp target={0.2} decimals={1} suffix="ms" className={`${styles.tval} ${styles.em}`} />
            <div className={styles.tval}>3.1ms</div>
            <div className={`${styles.tval} ${styles.gain} ${styles.colGain}`}>15.5× faster</div>
            <div className={`${styles.tcheck} ${styles.colCheck}`}><Check size={18} /></div>
          </Reveal>
          <Reveal delay={0.2} className={styles.trow}>
            <div className={styles.tmetric}>Hash Throughput</div>
            <CountUp target={184} suffix="K /s" className={`${styles.tval} ${styles.em}`} />
            <div className={styles.tval}>42K /s</div>
            <div className={`${styles.tval} ${styles.gain} ${styles.colGain}`}>4.4× higher</div>
            <div className={`${styles.tcheck} ${styles.colCheck}`}><Check size={18} /></div>
          </Reveal>
          <Reveal delay={0.3} className={styles.trow}>
            <div className={styles.tmetric}>Report Generation</div>
            <CountUp target={1.2} decimals={1} suffix="s" className={`${styles.tval} ${styles.em}`} />
            <div className={styles.tval}>18.5s</div>
            <div className={`${styles.tval} ${styles.gain} ${styles.colGain}`}>15× faster</div>
            <div className={`${styles.tcheck} ${styles.colCheck}`}><Check size={18} /></div>
          </Reveal>
          <Reveal delay={0.4} className={styles.trow}>
            <div className={styles.tmetric}>Threat Feed Sync</div>
            <CountUp target={99.99} decimals={2} suffix="%" className={`${styles.tval} ${styles.em}`} />
            <div className={styles.tval}>99.5%</div>
            <div className={`${styles.tval} ${styles.gain} ${styles.colGain}`}>+0.49 pts</div>
            <div className={`${styles.tcheck} ${styles.colCheck}`}><Check size={18} /></div>
          </Reveal>
        </div>
      </section>

      {/* CTA */}
      <section className={`${styles.container} ${styles.ctaSec}`}>
        <Reveal>
          <span className={styles.monoLabel}>/ 03 — Deploy</span>
          <h2>
            <span className={styles.gradientText}>Defend on the edge of what's possible.</span>
          </h2>
        </Reveal>
        <Reveal delay={0.2}>
          <div className={styles.btnRow} style={{ justifyContent: "center" }}>
            <Link href="/dashboard" className={`${styles.btn} ${styles.btnSolid} ${styles.bigPill}`} style={{ animation: "pulseGlow 3.2s cubic-bezier(0.16, 1, 0.3, 1) infinite" }}>
              Initialize Workbench <ArrowRight size={15} />
            </Link>
          </div>
        </Reveal>
      </section>

      {/* FOOTER */}
      <footer className={styles.footer}>
        <div className={`${styles.container} ${styles.footInner}`}>
          <div className={styles.logo}>
            <span className={styles.logoMark}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 3a3 3 0 0 0-3 3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3Z" />
              </svg>
            </span>
            <span className={styles.logoText}>PRATIKRIYA</span>
          </div>
          <span className={styles.monoLabel}>© 2026 PRATIKRIYA DFIR · Engineered for precision</span>
        </div>
      </footer>
    </div>
  );
}
