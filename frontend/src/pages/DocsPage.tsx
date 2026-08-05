import { useEffect } from 'react';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import './DocsPage.css';

export const DocsPage = () => {
  const copyToClipboard = (text: string, e: React.MouseEvent<HTMLButtonElement>) => {
    const btn = e.currentTarget;
    navigator.clipboard.writeText(text).then(() => {
      const originalSVG = btn.innerHTML;
      btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check"><polyline points="20 6 9 17 4 12"></polyline></svg>';
      btn.style.color = 'var(--lichen)';
      setTimeout(() => {
        btn.innerHTML = originalSVG;
        btn.style.color = '';
      }, 2000);
    });
  };

  const psCommand = 'iwr https://github.com/shivenducs1136/fungus/releases/download/v1.0.0/fungus-mcp.exe -OutFile fungus-mcp.exe; $j = (iwr https://github.com/shivenducs1136/fungus/releases/download/v1.0.0/mcp_distribution.json).Content | ConvertFrom-Json; $j.servers.\'fungus-knowledge\'.command = "$PWD\\fungus-mcp.exe"; $j | ConvertTo-Json -Depth 5 | Out-File mcp.json -Encoding utf8';

  useEffect(() => {
    const sections = Array.from(document.querySelectorAll('main h1, main h2, main h3')).filter(el => el.id);
    const navLinks = document.querySelectorAll('.sidebar-nav a');

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + entry.target.id) {
              link.classList.add('active');
            }
          });
        }
      });
    }, { rootMargin: '-40px 0px -80% 0px' });

    sections.forEach(section => observer.observe(section));

    return () => {
      sections.forEach(section => observer.unobserve(section));
    };
  }, []);

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement>, id: string) => {
    e.preventDefault();
    const target = document.getElementById(id);
    if (target) {
      window.scrollTo({
        top: target.offsetTop - 40,
        behavior: 'smooth'
      });
    }
  };

  return (
    <>
      <Header />
      <div className="plate-num mono">MANUAL OF BOTANICAL ENGINEERING — VOL. I</div>

      <div className="docs-wrap docs-container">
        <aside className="sidebar">
          <div className="sidebar-title">Index</div>
          <nav className="sidebar-nav">
            <a href="#getting-started" className="active" onClick={(e) => handleScroll(e, 'getting-started')}>Getting Started</a>
            <a href="#architecture" onClick={(e) => handleScroll(e, 'architecture')}>Architecture</a>
            <a href="#installation" onClick={(e) => handleScroll(e, 'installation')}>Installation</a>
            <a href="#usage" onClick={(e) => handleScroll(e, 'usage')}>Usage & MCP</a>
          </nav>
        </aside>
        
        <main className="main-content">
          <h1 id="getting-started">Getting Started</h1>
          <p>AI-assisted software development generates valuable architectural reasoning during implementation. The final code captures what was built, but not why a solution was chosen, the constraints discovered, or the tradeoffs considered.</p>
          <p>Fungus preserves that reasoning and links it directly to source code through Git history, ensuring it remains accessible to future developers and AI agents.</p>
          
          <div className="note">
            <p>The goal is to preserve implementation rationale so future developers and future AI agents can make informed decisions without repeating past investigations.</p>
          </div>
          
          <h2 id="architecture">Architecture</h2>
          <p>The Fungus ecosystem consists of two primary organisms:</p>
          <ol style={{ marginLeft: '20px', marginBottom: '20px', color: 'var(--ink-soft)', lineHeight: 1.7 }}>
            <li><strong>Knowledge Server:</strong> A robust FastAPI-based service providing knowledge storage, context retrieval, hash generation, and persistence.</li>
            <li><strong>MCP Server:</strong> A lightweight client-side standalone executable that handles Git operations and interacts with the Knowledge Server to save and retrieve context over stdio.</li>
          </ol>
          
          <h2 id="installation">Installation</h2>
          <p>The MCP server is packaged as a single <code>fungus-mcp.exe</code> file (~20 MB) so users need no Python installation.</p>
          
          <h3>1. Quick Install (Windows Release)</h3>
          <p>Open PowerShell in your preferred tooling directory and run this one-liner to download the executable and construct the <code>mcp.json</code> configuration file automatically:</p>
          <div className="code-copy-wrapper">
            <div className="code-content">{psCommand}</div>
            <button className="copy-btn" title="Copy to clipboard" onClick={(e) => copyToClipboard(psCommand, e)}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-copy"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            </button>
          </div>
          <p>This command dynamically injects the absolute path of the downloaded executable into your <code>mcp.json</code> file.</p>
          
          <h3>2. Building From Source</h3>
          <p>If you prefer to build the executable yourself from the latest source code:</p>
          <pre><code>{`git clone https://github.com/shivenducs1136/fungus.git\ncd fungus\n.\\build\\build_exe.ps1`}</code></pre>
          <p>This installs PyInstaller into the active virtual environment and produces <code>dist\fungus-mcp.exe</code>.</p>
        
          <h2 id="usage">Usage & MCP Configuration</h2>
          <p>Once you have the <code>mcp.json</code> file ready, configure your AI agent to use it. For Claude Desktop, simply append the servers block from <code>mcp.json</code> to your <code>claude_desktop_config.json</code>.</p>
          
          <p>For Cursor and VS Code, provide the path to your <code>mcp.json</code> or configure it directly in their respective UI settings.</p>
        </main>
      </div>

      <Footer />
    </>
  );
};
