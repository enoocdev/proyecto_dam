// Componente de elemento del menu que se muestra u oculta segun permisos
// collapsed=true → solo icono con tooltip; onNavigate → cierra drawer movil
import { Link, useLocation } from "react-router-dom";
import {
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Tooltip,
} from "@mui/material";
import "../styles/MainLayout.css";
import useAuth from "../hooks/useAuth";

function ProtecterMenuItem({ item, collapsed = false, onNavigate }) {
    const location = useLocation();
    const { hasPermission, isStaff, isSuperuser } = useAuth();

    if (!isSuperuser) {
        if (item.requireStaff && !isStaff) return null;
        if (item.requiredPermission && !hasPermission(item.requiredPermission)) return null;
    }

    return (
        <ListItem disablePadding>
            <Tooltip title={collapsed ? item.text : ''} placement="right" arrow>
                <ListItemButton
                    className="menu-item-btn"
                    component={Link}
                    to={item.path}
                    selected={location.pathname === item.path}
                    onClick={onNavigate}
                    sx={collapsed ? { justifyContent: 'center', px: 0 } : {}}
                >
                    <ListItemIcon sx={collapsed ? { minWidth: 0 } : {}}>
                        {item.icon}
                    </ListItemIcon>
                    {!collapsed && <ListItemText primary={item.text} />}
                </ListItemButton>
            </Tooltip>
        </ListItem>
    );
}

export default ProtecterMenuItem;