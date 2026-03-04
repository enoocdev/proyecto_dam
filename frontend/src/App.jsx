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

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route element={<ProtectedRoute><MainLayout/></ProtectedRoute>} >
          <Route path="/" element={<DashboardPage/>} />
          <Route path="/classroom" element={<Classroom></Classroom>} />
          <Route path="/network-device" element={<div>network-device ...</div>} />
          <Route path="/users" element={<Users/>} />
          <Route path="/users-groups" element={<UserGroups/>} />
          <Route path="/profile" element={<Profile/>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
