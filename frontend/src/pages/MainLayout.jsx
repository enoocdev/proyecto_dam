// Layout principal con barra lateral de navegacion y contenido dinamico
// Muestra u oculta opciones del menu segun los permisos del usuario
import { Outlet, Link, useLocation } from "react-router-dom"; 
import ProtecterMenuItem from "../components/ProtecterMenuItem";
import {
    Box,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
} from "@mui/material";
import LogoutIcon from '@mui/icons-material/Logout';
import ProfileIcon from '@mui/icons-material/Person';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SchoolIcon from '@mui/icons-material/School';
import RouterIcon from '@mui/icons-material/Router';
import PeopleIcon from '@mui/icons-material/People';
import GroupsIcon from '@mui/icons-material/Groups';
import DnsIcon from '@mui/icons-material/Dns';
import LightModeIcon from '@mui/icons-material/LightMode';
import DarkModeIcon from '@mui/icons-material/DarkMode';

import { useTheme } from '../context/ThemeContext';
import "../styles/MainLayout.css";

const drawerWidth = 260;

function MainLayout() {

    const location = useLocation(); 
    const { toggleTheme, isDark } = useTheme();

    const menuOptions = [
        { text: "Dashboard", icon: <DashboardIcon />, path: "/", requiredPermission: "view_device" },
        { text: "Classroom", icon: <SchoolIcon />, path: "/classroom", requiredPermission: "view_classroom", requireStaff: true },
        { text: "Switchs / routers", icon: <RouterIcon />, path: "/network-device", requiredPermission: "view_networkdevice", requireStaff: true },
        { text: "Hosts Permitidos", icon: <DnsIcon />, path: "/allowed-hosts", requiredPermission: "view_allowedhost", requireStaff: true },
        { text: "Usuarios", icon: <PeopleIcon />, path: "/users", requiredPermission: "view_user", requireStaff: true },
        { text: "Grupos", icon: <GroupsIcon />, path: "/users-groups", requiredPermission: "view_group", requireStaff: true },
    ];

    return (
        <Box className="layout-root">
            <Drawer
                className="layout-drawer"
                variant="permanent"
                sx={{
                    width: drawerWidth,
                    flexShrink: 0,
                    [`& .MuiDrawer-paper`]: {
                        width: drawerWidth,
                        boxSizing: "border-box",
                        border: "none" 
                    },
                }}
            >
                <Box className="sidebar-header">
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
                        Monitorización
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'var(--text-secondary)' }}>
                        Panel de Administración
                    </Typography>
                </Box>

                <Box sx={{ overflow: "auto", flexGrow: 1 }}>
                    <List>
                        {menuOptions.map((item, index) => (
                            <ProtecterMenuItem key={index} item={item} ></ProtecterMenuItem>
                        ))}
                    </List>
                </Box>


                <Box sx={{ mb: 2 }}>
                    <List>
                        <ListItem disablePadding>
                            <ListItemButton 
                                className="menu-item-btn theme-toggle-btn"
                                onClick={toggleTheme}
                            >
                                <ListItemIcon>
                                    {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                                </ListItemIcon>
                                <ListItemText primary={isDark ? 'Modo Claro' : 'Modo Oscuro'} />
                            </ListItemButton>
                        </ListItem>

                        <ListItem disablePadding>
                            <ListItemButton 
                                className="menu-item-btn"
                                component={Link} 
                                to={"/profile"}
                                selected={location.pathname === "/profile"}
                            >
                                <ListItemIcon>
                                    <ProfileIcon />
                                </ListItemIcon>
                                <ListItemText primary="Perfil" />
                            </ListItemButton>
                        </ListItem>

                        <ListItem disablePadding>
                            <ListItemButton 
                                className="menu-item-btn logout-btn"
                                component={Link} 
                                to={"/logout"}
                            >
                                <ListItemIcon>
                                    <LogoutIcon />
                                </ListItemIcon>
                                <ListItemText primary="Cerrar Sesion" />
                            </ListItemButton>
                        </ListItem>
                    </List>
                </Box>
            </Drawer>

            <Box component="main" className="layout-content">
                <Outlet />
            </Box>
        </Box>
    );
}

export default MainLayout;