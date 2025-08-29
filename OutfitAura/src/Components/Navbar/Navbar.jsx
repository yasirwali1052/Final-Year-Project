import { useState } from "react";
import { Link } from "react-scroll";
import { auth } from "../../firebase"; // Firebase import
import { signOut } from "firebase/auth";
import { useNavigate } from "react-router-dom";
import "./navbar.css";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await signOut(auth);
      navigate('/login');
    } catch (error) {
      console.error("Error signing out:", error);
    }
  };

  return (
    <nav className="navbar">
      <div className="logo">OutfitAura </div>
      <ul className={isOpen ? "nav-links open" : "nav-links"}>
        <li>
          <Link
            to="home"
            smooth={true}
            duration={500}
            onClick={() => setIsOpen(false)}
          >
            Home
          </Link>
        </li>
        <li>
          <Link
            to="how-it-works"
            smooth={true}
            duration={500}
            onClick={() => setIsOpen(false)}
          >
            How It Works
          </Link>
        </li>
        <li>
          <Link
            to="about"
            smooth={true}
            duration={500}
            onClick={() => setIsOpen(false)}
          >
            About
          </Link>
        </li>
        <li>
          <Link
            to="contact"
            smooth={true}
            duration={500}
            onClick={() => setIsOpen(false)}
          >
            Help Center
          </Link>
        </li>
        <button className="logout-btn" onClick={handleLogout}>
          LOGOUT
        </button>
      </ul>
      <div className="hamburger" onClick={() => setIsOpen(!isOpen)}>
        ☰
      </div>
    </nav>
  );
};

export default Navbar;
