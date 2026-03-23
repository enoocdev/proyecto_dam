// Componente que limpia el almacenamiento local y redirige al login
import { Navigate } from "react-router-dom";
import { clearUserClassrooms } from '../stores/userClassroomsStore';

function Logout(){

    localStorage.clear()
    clearUserClassrooms()
    return <Navigate to={"/login"} replace></Navigate>
}

export default Logout