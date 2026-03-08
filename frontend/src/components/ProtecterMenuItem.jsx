// Componente de elemento del menu que se muestra u oculta segun permisos
// Renderiza un enlace de navegacion solo si el usuario tiene acceso
import { Link, useLocation } from "react-router-dom";
import {
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
} from "@mui/material";
import "../styles/MainLayout.css";
import useAuth from "../hooks/useAuth";

function ProtecterMenuItem({ item }) {
    const location = useLocation();
    const { hasPermission, isStaff, isSuperuser } = useAuth();

    // Los superusuarios ven todos los elementos del menu
    if (!isSuperuser) {
        // Oculta el elemento si requiere staff y el usuario no lo es
        if (item.requireStaff && !isStaff) return null;

        // Oculta el elemento si no tiene el permiso requerido
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