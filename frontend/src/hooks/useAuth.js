import { useMemo } from "react";
import { USER_PERMISSIONS } from "../constants";

/**
 * Hook que lee los datos del usuario autenticado desde localStorage
 * y proporciona helpers para comprobar permisos.
 *
 * Django almacena los permisos como strings "app_label.codename",
 * por ejemplo: "auth.view_user", "devices.view_device", etc.
 *
 * Uso:
 *   const { hasPermission, isStaff, isSuperuser } = useAuth();
 *   if (hasPermission("view_device")) { ... }
 */
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

    /**
     * Comprueba si el usuario tiene un permiso concreto.
     * Acepta el codename corto ("view_device") o completo ("devices.view_device").
     * Los superusuarios siempre tienen todos los permisos.
     */
    const hasPermission = (codename) => {
        if (isSuperuser) return true;
        if (!codename) return true; // sin requisito → acceso libre

        // Coincidencia exacta ("devices.view_device") o por sufijo (".view_device" / "view_device")
        return permissions.some(
            (p) => p === codename || p.endsWith(`.${codename}`)
        );
    };

    return { hasPermission, isStaff, isSuperuser, permissions };
};

export default useAuth;
