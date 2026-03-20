// Componente principal que define las rutas de la aplicacion
// Cada ruta protegida verifica permisos antes de mostrar el contenido
import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import Login from "./pages/Login";
import Logout from "./components/Logout";
import Profile from "./pages/Profile";
import ProtectedRoute from "./components/ProtecterRoute";
import MainLayout from "./pages/MainLayout";
import "./App.css"
import UserGroups from "./pages/UserGroups";
import Users from "./pages/Users";
import { Dashboard } from "@mui/icons-material";
import DashboardPage from "./pages/Dashboard";
import Classroom from "./pages/Classrooms";
import NetworkDevices from "./pages/NetworkDevices";

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route element={<ProtectedRoute><MainLayout/></ProtectedRoute>} >
          <Route path="/" element={<ProtectedRoute requiredPermission="view_device"><DashboardPage/></ProtectedRoute>} />
          <Route path="/classroom" element={<ProtectedRoute requiredPermission="view_classroom"><Classroom/></ProtectedRoute>} />
          <Route path="/network-device" element={<ProtectedRoute requiredPermission="view_networkdevice"><NetworkDevices/></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute requiredPermission="view_user" requireStaff><Users/></ProtectedRoute>} />
          <Route path="/users-groups" element={<ProtectedRoute requiredPermission="view_group" requireStaff><UserGroups/></ProtectedRoute>} />
          <Route path="/profile" element={<Profile/>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
