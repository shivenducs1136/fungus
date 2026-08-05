import { Link } from 'react-router-dom';

export const Header = () => {
  return (
    <header>
      <div className="wrap head-row">
        <div className="logo">fungus</div>
        <nav>
          <Link to="/">home</Link>
          <Link to="/docs">docs</Link>
          <Link to="/dashboard">dashboard</Link>
        </nav>
      </div>
    </header>
  );
};
