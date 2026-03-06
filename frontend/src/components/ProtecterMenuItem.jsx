import { Link, useLocation } from "react-router-dom";
import {
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
} from "@mui/material";
import "../styles/MainLayout.css";
import useAuth from "../hooks/useAuth";

/**
 * Muestra u oculta un elemento del menú según los permisos del usuario.
 *
 * Props esperadas en `item`:
 *   - requiredPermission: codename del permiso necesario (ej. "view_device")
 *   - requireStaff:       si true, el usuario debe ser staff
 */
function ProtecterMenuItem({ item }) {
    const location = useLocation();
    const { hasPermission, isStaff, isSuperuser } = useAuth();

    // Superusuarios ven todo
    if (!isSuperuser) {
        // Comprobar si requiere staff
        if (item.requireStaff && !isStaff) return null;

        // Comprobar permiso concreto
        if (item.requiredPermission && !hasPermission(item.requiredPermission)) return null;
    }

    return (
        <ListItem disablePadding>
            <ListItemButton
                className="menu-item-btn"
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
            >
                <ListItemIcon>
                    {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
            </ListItemButton>
        </ListItem>
    );
}

export default ProtecterMenuItem;