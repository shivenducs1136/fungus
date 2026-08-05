export const Footer = () => {
  return (
    <footer>
      <div className="wrap foot-row" style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        <div style={{ display: 'flex', gap: '16px' }}>
          <span>fungus — field edition</span>
          <span>an MCP server for legacy code</span>
        </div>
        <div style={{ display: 'flex', gap: '16px', color: 'var(--ink)' }}>
          <span>
            Mycologists: <a href="https://github.com/girishnaman" target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>girishnaman (Girish Gupta)</a> & <a href="https://github.com/shivenducs1136/" target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'underline' }}>shivenducs1136 (Shivendu Mishra)</a>
          </span>
        </div>
      </div>
    </footer>
  );
};
