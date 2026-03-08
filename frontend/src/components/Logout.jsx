// Componente que limpia el almacenamiento local y redirige al login
import { Navigate } from "react-router-dom";

function Logout(){

    localStorage.clear()
    return <Navigate to={"/login"} replace></Navigate>
}

export default Logout