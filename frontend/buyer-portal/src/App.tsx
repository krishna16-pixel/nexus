import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { BookDetail } from "./pages/BookDetail";
import { Buddy } from "./pages/Buddy";
import { CartPage } from "./pages/Cart";
import { Catalog } from "./pages/Catalog";
import { Checkout } from "./pages/Checkout";
import { Circle } from "./pages/Circle";
import { Detective } from "./pages/Detective";
import { Login } from "./pages/Login";
import { Mystery } from "./pages/Mystery";
import { Notifications } from "./pages/Notifications";
import { OrderDetail } from "./pages/OrderDetail";
import { Orders } from "./pages/Orders";
import { Passport } from "./pages/Passport";
import { Price } from "./pages/Price";
import { Register } from "./pages/Register";
import { Rentals } from "./pages/Rentals";
import { Wishlist } from "./pages/Wishlist";

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Loading...</div>;
  if (user) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
          <Route path="/register" element={<PublicOnly><Register /></PublicOnly>} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Catalog />} />
            <Route path="books/:id" element={<BookDetail />} />
            <Route path="cart" element={<CartPage />} />
            <Route path="checkout" element={<Checkout />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:id" element={<OrderDetail />} />
            <Route path="circle" element={<Circle />} />
            <Route path="buddy" element={<Buddy />} />
            <Route path="price" element={<Price />} />
            <Route path="detective" element={<Detective />} />
            <Route path="passport" element={<Passport />} />
            <Route path="mystery" element={<Mystery />} />
            <Route path="wishlist" element={<Wishlist />} />
            <Route path="rentals" element={<Rentals />} />
            <Route path="notifications" element={<Notifications />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
