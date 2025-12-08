import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Logout from "./components/Logout";
import ProtectedRoute from "./components/ProtecterRoute";
import "./App.css"

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route element={<ProtectedRoute><div>Cargando Django ...</div></ProtectedRoute>} >
          <Route path="/" element={<div>Dashboard ...</div>} />
          <Route path="/profile" element={<div>Profile ...</div>} />
        </Route>

      </Routes>
    </BrowserRouter>
  )
}

export default App
