import { BrowserRouter, Routes, Route, Outlet } from "react-router-dom";
import Login from "./pages/Login";
import Logout from "./components/Logout";
import Profile from "./pages/Profile";
import ProtectedRoute from "./components/ProtecterRoute";
import MainLayout from "./pages/MainLayout";
import "./App.css"

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route element={<ProtectedRoute><MainLayout/></ProtectedRoute>} >
          <Route path="/" element={<div>Dashboard ...</div>} />
          <Route path="/classroom" element={<div>classrooms ...</div>} />
          <Route path="/network-device" element={<div>network-device ...</div>} />
          <Route path="/profile" element={<Profile/>} />
          <Route path="/users" element={<div>users ...</div>} />
          <Route path="/users-groups" element={<div>users-groups ...</div>} />
          <Route path="/permissions" element={<div>permissions ...</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
