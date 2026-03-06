import { Navigate } from "react-router-dom";
import { ACCESS_TOKEN } from "../constants";
import useAuth from "../hooks/useAuth";
import RestrictedAccess from "./RestrictedAccess";

/**
 * Protege una ruta.
 *
 * Sin props extra → solo requiere token (estar logueado).
 * Con requiredPermission / requireStaff → comprueba permisos.
 */
function ProtectedRoute({ children, requiredPermission, requireStaff }) {
    const token = localStorage.getItem(ACCESS_TOKEN);
    const { hasPermission, isStaff, isSuperuser } = useAuth();

    if (!token) return <Navigate to="/login" replace />;

    // Comprobar permisos adicionales (superusers pasan siempre)
    if (!isSuperuser) {
        if (requireStaff && !isStaff) return <RestrictedAccess />;
        if (requiredPermission && !hasPermission(requiredPermission)) return <RestrictedAccess />;
    }

    return children;
}

export default ProtectedRoute;