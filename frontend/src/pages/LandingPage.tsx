import { Link } from 'react-router-dom';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import './LandingPage.css';

export const LandingPage = () => {
  const copyToClipboard = (text: string, e: React.MouseEvent<HTMLButtonElement>) => {
    const btn = e.currentTarget;
    navigator.clipboard.writeText(text).then(() => {
      const originalSVG = btn.innerHTML;
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check"><polyline points="20 6 9 17 4 12"></polyline></svg>';
      btn.style.color = 'var(--lichen)';
      setTimeout(() => {
        btn.innerHTML = originalSVG;
        btn.style.color = '';
      }, 2000);
    });
  };

  const psCommand = 'iwr https://github.com/shivenducs1136/fungus/releases/download/v1.0.0/fungus-mcp.exe -OutFile fungus-mcp.exe; $j = (iwr https://github.com/shivenducs1136/fungus/releases/download/v1.0.0/mcp_distribution.json).Content | ConvertFrom-Json; $j.servers.\'fungus-knowledge\'.command = "$PWD\\fungus-mcp.exe"; $j | ConvertTo-Json -Depth 5 | Out-File mcp.json -Encoding utf8';

  return (
    <>
      <Header />
      <div className="plate-num mono">PLATE VII — CONTEXT-BEARING SPECIES, DOMESTICATED FOR SOFTWARE REPOSITORIES</div>

      <section className="hero">
        <div className="wrap hero-grid">
          <div>
            <div className="eyebrow">MCP server, field edition</div>
            <h1>Legacy code has a memory.<br/>It's just <i>underground</i>.</h1>
            <p className="sub">Fungus collects the context your agents already worked out — the why behind the weird function — and roots it to the code itself via Git commits, so it resurfaces exactly when it's needed again.</p>
            <p className="latin">Context perennis, sub cortice repositum.</p>
          </div>

          <div className="specimen">
            <span className="specimen-label mono">fig. 1 — mycelial attachment</span>
            <svg viewBox="0 0 400 380">
              <path d="M120 150 C 120 90, 160 55, 200 55 C 240 55, 280 90, 280 150 Z" fill="none" stroke="#26221A" strokeWidth="1.6"/>
              <path d="M130 150 C130 100, 165 68, 200 68 C 235 68, 270 100, 270 150" fill="none" stroke="#9C5B3C" strokeWidth="1" opacity="0.5"/>
              <g stroke="#26221A" strokeWidth="0.8" opacity="0.55">
                <line x1="140" y1="150" x2="145" y2="130"/>
                <line x1="155" y1="150" x2="162" y2="120"/>
                <line x1="172" y1="150" x2="178" y2="112"/>
                <line x1="190" y1="150" x2="192" y2="108"/>
                <line x1="208" y1="150" x2="208" y2="108"/>
                <line x1="226" y1="150" x2="222" y2="112"/>
                <line x1="244" y1="150" x2="238" y2="120"/>
                <line x1="260" y1="150" x2="255" y2="130"/>
              </g>
              <rect x="188" y="150" width="24" height="70" fill="none" stroke="#26221A" strokeWidth="1.6"/>
              <g fill="none" stroke="#5C6B4F" strokeWidth="1.2">
                <path d="M195 220 C 170 240, 150 250, 110 265"/>
                <path d="M200 220 C 195 250, 195 270, 190 310"/>
                <path d="M206 220 C 235 245, 250 255, 290 270"/>
                <path d="M110 265 C 80 280, 60 300, 40 330"/>
                <path d="M110 265 C 100 290, 90 305, 95 335"/>
                <path d="M290 270 C 310 290, 330 300, 355 320"/>
                <path d="M190 310 C 175 330, 165 340, 150 360"/>
              </g>
              <circle cx="110" cy="265" r="3" fill="#B8934A"/>
              <circle cx="290" cy="270" r="3" fill="#B8934A"/>
              <circle cx="190" cy="310" r="3" fill="#B8934A"/>
              <circle cx="40" cy="330" r="2.4" fill="#26221A"/>
              <circle cx="95" cy="335" r="2.4" fill="#26221A"/>
              <circle cx="355" cy="320" r="2.4" fill="#26221A"/>
              <circle cx="150" cy="360" r="2.4" fill="#26221A"/>
              <text x="10" y="352" className="mono" fontSize="8.5" fill="#5B5648">auth.py</text>
              <text x="60" y="352" className="mono" fontSize="8.5" fill="#5B5648">migrate_v2</text>
              <text x="300" y="336" className="mono" fontSize="8.5" fill="#5B5648">worker.rb</text>
              <text x="118" y="376" className="mono" fontSize="8.5" fill="#5B5648">test_suite</text>
            </svg>
            <div className="specimen-caption">
              <span>a. fruiting body — the surfaced answer</span>
              <span>b. rhizomorph — the trace to the commit hash</span>
            </div>
          </div>
        </div>
      </section>

      <section className="collect" id="collect">
        <div className="wrap">
          <div className="label-box">
            <div className="label-head">
              <span>specimen no. 001 — client installation (windows release)</span>
              <span>coll. local-machine/</span>
            </div>
            <div className="label-body">
              <div className="r1" style={{marginBottom: '8px'}}># Paste in PowerShell to download the executable and configure mcp.json in the current folder</div>
              <div className="code-copy-wrapper">
                <div className="code-content c1">{psCommand}</div>
                <button className="copy-btn" title="Copy to clipboard" onClick={(e) => copyToClipboard(psCommand, e)}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-copy"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                </button>
              </div>
            </div>
            <div className="label-foot">
              <span>Downloads the v1.0.0 self-contained MCP server (~20 MB)</span>
              <span>Generates a ready-to-use mcp.json</span>
            </div>
          </div>
          
          <div className="label-box">
            <div className="label-head">
              <span>specimen no. 002 — building from source</span>
              <span>coll. local-repo/</span>
            </div>
            <div className="label-body">
              <div className="r1" style={{marginBottom: '8px'}}># Clone the repository and build the executable locally</div>
              <div><span className="p1">PS &gt;</span> <span className="c1">git clone https://github.com/shivenducs1136/fungus.git</span></div>
              <div><span className="p1">PS &gt;</span> <span className="c1">cd fungus</span></div>
              <div><span className="p1">PS &gt;</span> <span className="c1">.\build\build_exe.ps1</span></div>
            </div>
            <div className="label-foot">
              <span>Installs PyInstaller into the active venv</span>
              <span>Produces dist\fungus-mcp.exe</span>
            </div>
          </div>
        </div>
      </section>

      <section className="key" id="key">
        <div className="wrap">
          <div className="key-head">
            <div className="section-label">Field key</div>
            <h2>What gets pressed into the record, and where it resurfaces.</h2>
          </div>
          <div className="keylist">
            <div className="keyitem">
              <div className="letter">a</div>
              <div>
                <h3>Working notes, kept</h3>
                <p>Whatever an agent or engineer figures out mid-session — the reason for the odd branch, the migration that never got documented — gets written to the file it concerns, not lost to a closed tab.</p>
              </div>
            </div>
            <div className="keyitem">
              <div className="letter">b</div>
              <div>
                <h3>Rooted to Git History</h3>
                <p>Context spreads along real dependencies. By linking the deep knowledge document to a context hash (ctx-xxxx) in the Git Commit Message, the information is bound to the exact point in time the codebase changed.</p>
              </div>
            </div>
            <div className="keyitem">
              <div className="letter">c</div>
              <div>
                <h3>Any agent can read it</h3>
                <p>Served over MCP. Claude, Cursor, or your own scripts all pull from the same accumulated record — nothing re-explained twice. No vector databases, embeddings, or RAG needed. O(1) retrieval.</p>
              </div>
            </div>
            <div className="keyitem">
              <div className="letter">d</div>
              <div>
                <h3>The codebase speaks for itself</h3>
                <p>When you ask "Why is this implemented this way?", Fungus performs a git blame, retrieves the commit, extracts the key, and serves the rationale perfectly.</p>
              </div>
            </div>
          </div>

          <div className="example-ui-title">fig. 2 — extracting context from a commit</div>
          <div className="journal-container">
            <div style={{background: 'var(--paper-2)', border: '1px dashed var(--line)', padding: '15px 20px', fontSize: '13px', color: 'var(--ink-soft)', fontFamily: "'Source Serif 4', serif"}}>
              <span style={{fontFamily: "'Space Mono',monospace", fontSize: '10px', textTransform: 'uppercase', color: 'var(--lichen)', display: 'block', marginBottom: '8px'}}>Context from architecture knowledge:</span>
              This calculator was created by Shivendu (TPR-111/TPR-121) as a sample/POC app intended for use in Tally Prime's Calculator Panel. It supports the standard operators plus two custom operators: tilda ( ~ ) for dual negation and power ( ^ ).<br/><br/>
              The function is simple and straightforward—it's a dispatcher that routes to the appropriate operation based on the operator symbol.
            </div>

            <div className="entry-user">
              <div className="query-text">why these two custom operator impl?</div>
            </div>

            <div className="entry-tool">
              <div className="tool-status">Let me check the commit history and knowledge base for context on why these operators were added.</div>
              <div className="tool-box">
                <div><span className="tool-name">Fungus-knowledge</span> [retrieve_knowledge]</div>
                <div className="tool-out">OUT {"{\"message\":\"**Knowledge Summary for TPR-3001**\\nEntries included: 1\\n**Combined Summary**\\nProblem: Exponential UI calculations...\"}"}</div>
              </div>
            </div>

            <div className="entry-agent">
              <div className="agent-label">Findings Documented</div>
              <div className="agent-content">
                <p>Here's why these operators were added:</p>
                
                <h3>1. Tilda ( ~ ) operator <span className="commit-ref">ref: TPR-2093</span></h3>
                <ul>
                  <li><strong>Added by:</strong> Deva Harsha BT for the Custom PDF Engine.</li>
                  <li><strong>Purpose:</strong> String position calculation — calculates position accurately for each word in a string.</li>
                  <li><strong>Implementation:</strong> <code>a*-1 + b*-1</code> negates both operands and sums them.</li>
                </ul>
                
                <h3>2. Power ( ^ ) operator <span className="commit-ref">ref: TPR-3001</span></h3>
                <ul>
                  <li><strong>Added by:</strong> Yashas and Yashwanth for the UI team.</li>
                  <li><strong>Purpose:</strong> Exponential zone calculations in the UI.</li>
                  <li><strong>Implementation:</strong> <code>a ** b</code> (standard Python exponentiation).</li>
                </ul>
                
                <p>Both were domain-specific requirements: the tilda operator supports the PDF engine's text positioning logic. They're not general-purpose calculator features—they're specialized for Tally Prime's specific use cases.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="press">
        <div className="wrap">
          <h2>Stop letting good answers evaporate.</h2>
          <p>Read the documentation to learn how to plant the spores in your infrastructure.</p>
          <Link to="/docs" className="btn">View Documentation</Link>
        </div>
      </section>

      <Footer />
    </>
  );
};
