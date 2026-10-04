import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { BookForm } from "./pages/BookForm";
import { Books } from "./pages/Books";
import { BulkBooks } from "./pages/BulkBooks";
import { Buddy } from "./pages/Buddy";
import { Circle } from "./pages/Circle";
import { Dashboard } from "./pages/Dashboard";
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
import { Reviews } from "./pages/Reviews";
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
            <Route index element={<Dashboard />} />
            <Route path="books" element={<Books />} />
            <Route path="books/new" element={<BookForm />} />
            <Route path="books/bulk" element={<BulkBooks />} />
            <Route path="books/:id/edit" element={<BookForm />} />
            <Route path="orders" element={<Orders />} />
            <Route path="orders/:id" element={<OrderDetail />} />
            <Route path="reviews" element={<Reviews />} />
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
