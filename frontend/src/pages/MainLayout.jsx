import { Outlet, Link, useLocation } from "react-router-dom"; 
import ProtecterMenuItem from "../components/ProtecterMenuitem";
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

import "../styles/MainLayout.css";

const drawerWidth = 260;

function MainLayout() {

    const location = useLocation(); 

    const menuOptions = [
        { text: "Dashboard", icon: <DashboardIcon />, path: "/", apiPath : "/devices/devices/"},
        { text: "Classroom", icon: <SchoolIcon />, path: "/classroom", apiPath : "/devices/classroom/"},
        { text: "Switchs / routers", icon: <RouterIcon />, path: "/network-device",apiPath : "/devices/network-device/"},
        { text: "permisos", icon: <RouterIcon />, path: "/permissions",apiPath : "/permissions/"}
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
                    <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'white' }}>
                        Monitorización
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#aaa' }}>
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