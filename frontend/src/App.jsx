import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import ProtectedRoute from "./components/ProtecterRoute";
import "./App.css"

function App() {

  return (
    <BrowserRouter>
      <Routes>
        
        <Route 
          path="/" 
          element={
            <ProtectedRoute>
              <div>
                Cargando Django ...
              </div>
            </ProtectedRoute>
          } 
        />

        <Route path="/login" element={<Login />} />
        
      </Routes>
    </BrowserRouter>
  )
}

export default App
