const SELLER_URL = import.meta.env.VITE_SELLER_PORTAL_URL || "http://localhost:5173";
const BUYER_URL = import.meta.env.VITE_BUYER_PORTAL_URL || "http://localhost:5174";

export default function App() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <a href="/" className="landing-logo">
          <span className="landing-logo-mark">📚</span>
          <span className="landing-logo-text">BookVerse</span>
        </a>
        <div className="landing-nav-links">
          <a href="#portals">Portals</a>
          <a href="#journey">Journey</a>
          <a href="#features">Features</a>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="landing-hero-bg" />
        <span className="landing-deco landing-deco-1" aria-hidden>📖</span>
        <span className="landing-deco landing-deco-2" aria-hidden>📕</span>
        <span className="landing-deco landing-deco-3" aria-hidden>📗</span>

        <div className="landing-hero-content">
          <div className="landing-eyebrow">
            <span className="landing-eyebrow-dot" />
            Your marketplace for books
          </div>
          <h1>Buy and sell books with confidence</h1>
          <p className="landing-hero-sub">
            BookVerse connects independent sellers with readers worldwide. List your catalog,
            accept cash-on-delivery orders, and build trust through ratings.
          </p>

          <div id="portals" className="portal-cards">
            <a href={SELLER_URL} className="portal-card portal-card-seller">
              <div className="portal-card-icon">🏪</div>
              <h2>Seller Portal</h2>
              <p>
                Manage your inventory, fulfill orders, assign couriers, and grow your book business
                from one dashboard.
              </p>
              <span className="portal-card-cta">
                Enter seller portal
                <span className="portal-card-arrow">→</span>
              </span>
            </a>

            <a href={BUYER_URL} className="portal-card portal-card-buyer">
              <div className="portal-card-icon">🛒</div>
              <h2>Buyer Portal</h2>
              <p>
                Browse thousands of titles, shop with cart checkout, pay on delivery, and rate
                sellers and couriers.
              </p>
              <span className="portal-card-cta">
                Start shopping
                <span className="portal-card-arrow">→</span>
              </span>
            </a>
          </div>
        </div>
      </section>

      <section id="journey" className="landing-features">
        <div className="landing-features-inner">
          <h2>BookCircle — books keep circulating</h2>
          <p className="landing-features-sub">
            Read it → Circle it → Swap it → Buddy up → Wish it together
          </p>
          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-icon">📚</div>
              <h3>BookCircle</h3>
              <p>Sell, rent or donate read books to the next reader.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔄</div>
              <h3>Book Swap</h3>
              <p>Money-free “my book ↔ your book” exchange.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🧑‍🤝‍🧑</div>
              <h3>Study Buddy Match</h3>
              <p>Connect users reading the same book.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📍</div>
              <h3>Campus Exchange</h3>
              <p>College students exchange books within their college.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">💰</div>
              <h3>Fair Price Calculator</h3>
              <p>Suggested resale price from condition, edition and age.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🕵️</div>
              <h3>Book Detective</h3>
              <p>Rare and old books traced across sellers.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📖</div>
              <h3>Book Passport</h3>
              <p>Previous owners and readers of every second-hand book.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎁</div>
              <h3>Mystery Match</h3>
              <p>A surprise book from your interests.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📝</div>
              <h3>Reader Notes</h3>
              <p>Highlights and notes left by previous readers.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🤝</div>
              <h3>Community Wishlist</h3>
              <p>Same-book wishes grouped for bulk purchase.</p>
            </div>
          </div>
          <p className="landing-features-sub" style={{ marginTop: "1.5rem" }}>
            <a href={BUYER_URL + "/circle"}>BookCircle →</a>
            {" · "}
            <a href={BUYER_URL + "/buddy"}>Find buddies →</a>
            {" · "}
            <a href={BUYER_URL + "/wishlist"}>Wishlist →</a>
          </p>
        </div>
      </section>

      <section id="features" className="landing-features">
        <div className="landing-features-inner">
          <h2>Everything you need</h2>
          <p className="landing-features-sub">
            A complete platform built for sellers and buyers alike.
          </p>
          <div className="features-grid">
            <div className="feature-item">
              <div className="feature-icon">📦</div>
              <h3>Inventory management</h3>
              <p>Add books individually or in bulk. Control stock and visibility in real time.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">💵</div>
              <h3>Cash on delivery</h3>
              <p>Simple COD checkout splits orders by seller for smooth fulfillment.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">⭐</div>
              <h3>Trust & ratings</h3>
              <p>Buyers rate sellers and courier partners after every delivered order.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🚚</div>
              <h3>Order tracking</h3>
              <p>From placed to delivered — full visibility for sellers and buyers.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔐</div>
              <h3>Secure accounts</h3>
              <p>Separate seller and buyer roles with JWT authentication.</p>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🛍️</div>
              <h3>Smart cart</h3>
              <p>Multi-seller cart with automatic order splitting at checkout.</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <p>
          © {new Date().getFullYear()} BookVerse ·{" "}
          <a href={SELLER_URL}>Seller</a> · <a href={BUYER_URL}>Buyer</a>
        </p>
      </footer>
    </div>
  );
}
