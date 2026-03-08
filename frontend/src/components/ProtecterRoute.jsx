// Componente que protege rutas verificando autenticacion y permisos
// Sin props adicionales solo requiere estar logueado
// Con requiredPermission o requireStaff comprueba permisos especificos
import { Navigate } from "react-router-dom";
import { ACCESS_TOKEN } from "../constants";
import useAuth from "../hooks/useAuth";
import RestrictedAccess from "./RestrictedAccess";

function ProtectedRoute({ children, requiredPermission, requireStaff }) {
    const token = localStorage.getItem(ACCESS_TOKEN);
    const { hasPermission, isStaff, isSuperuser } = useAuth();

    if (!token) return <Navigate to="/login" replace />;

    // Los superusuarios tienen acceso total sin restricciones
    if (!isSuperuser) {
        if (requireStaff && !isStaff) return <RestrictedAccess />;
        if (requiredPermission && !hasPermission(requiredPermission)) return <RestrictedAccess />;
    }

    return children;
}

export default ProtectedRoute;