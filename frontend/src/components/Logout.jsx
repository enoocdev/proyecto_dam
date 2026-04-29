// Componente que limpia el almacenamiento local y redirige al login
import { Navigate } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN, USER_PERMISSIONS } from "../constants";
import { clearUserClassrooms } from '../stores/userClassroomsStore';

function Logout(){
    localStorage.removeItem(ACCESS_TOKEN);
    localStorage.removeItem(REFRESH_TOKEN);
    localStorage.removeItem(USER_PERMISSIONS);
    clearUserClassrooms()
    return <Navigate to={"/login"} replace></Navigate>
}

export default Logout