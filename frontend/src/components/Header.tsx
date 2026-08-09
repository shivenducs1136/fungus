import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BookDemoModal } from './BookDemoModal';

export const Header = () => {
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  return (
    <>
      <header>
        <div className="wrap head-row">
          <div className="logo">fungus</div>
          <nav style={{ alignItems: 'center' }}>
            <Link to="/">home</Link>
            <Link to="/docs">docs</Link>
            <button
              type="button"
              className="nav-book-demo-btn"
              onClick={() => setIsDemoModalOpen(true)}
            >
              Book Demo
            </button>
          </nav>
        </div>
      </header>

      <BookDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </>
  );
};

