// Hook que lee los datos del usuario autenticado desde localStorage
// Proporciona funciones para comprobar permisos y roles
import { useMemo } from "react";
import { USER_PERMISSIONS } from "../constants";

const useAuth = () => {
    const userData = useMemo(() => {
        try {
            const raw = localStorage.getItem(USER_PERMISSIONS);
            return raw ? JSON.parse(raw) : {};
        } catch {
            return {};
        }
    }, []);

    const permissions = userData.permissions || [];
    const isSuperuser = !!userData.is_superuser;
    const isStaff = !!userData.is_staff;

    // Comprueba si el usuario tiene un permiso concreto
    // Acepta el codename corto o completo con app label
    // Los superusuarios siempre tienen todos los permisos
    const hasPermission = (codename) => {
        if (isSuperuser) return true;
        if (!codename) return true;

        // Coincidencia exacta o por sufijo del nombre del permiso
        return permissions.some(
            (p) => p === codename || p.endsWith(`.${codename}`)
        );
    };

    return { hasPermission, isStaff, isSuperuser, permissions };
};

export default useAuth;
