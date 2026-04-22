// Layout principal con barra lateral de navegacion y contenido dinamico
// Muestra u oculta opciones del menu segun los permisos del usuario
// Responsive: drawer temporal en movil, sidebar iconos en tablet, sidebar completo en desktop
import { useState } from "react";
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
    AppBar,
    Toolbar,
    IconButton,
    Tooltip,
    useMediaQuery,
    useTheme as useMuiTheme,
    Divider,
} from "@mui/material";
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
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

const DRAWER_FULL = 260;
const DRAWER_MINI = 72;

function MainLayout() {

    const location = useLocation();
    const { toggleTheme, isDark } = useTheme();

    const muiTheme = useMuiTheme();
    const isMobile  = useMediaQuery(muiTheme.breakpoints.down('sm'));          // < 600px
    const isTablet  = useMediaQuery(muiTheme.breakpoints.between('sm', 'md')); // 600-960px
    const isDesktop = useMediaQuery(muiTheme.breakpoints.up('md'));             // >= 960px

    const [mobileOpen,       setMobileOpen]       = useState(false);
    const [desktopCollapsed, setDesktopCollapsed] = useState(false);

    const isCollapsed = isTablet || (isDesktop && desktopCollapsed);
    const drawerWidth = isCollapsed ? DRAWER_MINI : DRAWER_FULL;

    const menuOptions = [
        { text: "Dashboard",         icon: <DashboardIcon />, path: "/",              requiredPermission: "view_device" },
        { text: "Aulas",             icon: <SchoolIcon />,    path: "/classroom",     requiredPermission: "view_classroom",    requireStaff: true },
        { text: "Switchs / Routers", icon: <RouterIcon />,    path: "/network-device",requiredPermission: "view_networkdevice", requireStaff: true },
        { text: "Hosts Permitidos",  icon: <DnsIcon />,       path: "/allowed-hosts", requiredPermission: "view_allowedhost",  requireStaff: true },
        { text: "Usuarios",          icon: <PeopleIcon />,    path: "/users",         requiredPermission: "view_user",         requireStaff: true },
        { text: "Grupos",            icon: <GroupsIcon />,    path: "/users-groups",  requiredPermission: "view_group",        requireStaff: true },
    ];

    // Contenido compartido del drawer
    const drawerContent = (collapsed) => (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>

            {/* Cabecera */}
            <Box className={`sidebar-header${collapsed ? ' sidebar-header--collapsed' : ''}`}>
                {collapsed ? (
                    <Typography variant="h6" sx={{ fontWeight: 900, color: 'var(--accent-color)', textAlign: 'center' }}>
                        M
                    </Typography>
                ) : (
                    <>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
                            Monitorización
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'var(--text-secondary)' }}>
                            Panel de Administración
                        </Typography>
                    </>
                )}
            </Box>

            {/* Opciones de navegacion */}
            <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
                <List>
                    {menuOptions.map((item, index) => (
                        <ProtecterMenuItem
                            key={index}
                            item={item}
                            collapsed={collapsed}
                            onNavigate={() => setMobileOpen(false)}
                        />
                    ))}
                </List>
            </Box>

            <Divider sx={{ borderColor: 'var(--border-color)' }} />

            {/* Footer: tema, perfil, logout */}
            <Box sx={{ py: 1 }}>
                <List disablePadding>

                    <ListItem disablePadding>
                        <Tooltip title={collapsed ? (isDark ? 'Modo Claro' : 'Modo Oscuro') : ''} placement="right">
                            <ListItemButton
                                className="menu-item-btn theme-toggle-btn"
                                onClick={toggleTheme}
                                sx={collapsed ? { justifyContent: 'center', px: 0 } : {}}
                            >
                                <ListItemIcon sx={collapsed ? { minWidth: 0 } : {}}>
                                    {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                                </ListItemIcon>
                                {!collapsed && <ListItemText primary={isDark ? 'Modo Claro' : 'Modo Oscuro'} />}
                            </ListItemButton>
                        </Tooltip>
                    </ListItem>

                    <ListItem disablePadding>
                        <Tooltip title={collapsed ? 'Perfil' : ''} placement="right">
                            <ListItemButton
                                className="menu-item-btn"
                                component={Link}
                                to="/profile"
                                selected={location.pathname === '/profile'}
                                onClick={() => setMobileOpen(false)}
                                sx={collapsed ? { justifyContent: 'center', px: 0 } : {}}
                            >
                                <ListItemIcon sx={collapsed ? { minWidth: 0 } : {}}>
                                    <ProfileIcon />
                                </ListItemIcon>
                                {!collapsed && <ListItemText primary="Perfil" />}
                            </ListItemButton>
                        </Tooltip>
                    </ListItem>

                    <ListItem disablePadding>
                        <Tooltip title={collapsed ? 'Cerrar Sesión' : ''} placement="right">
                            <ListItemButton
                                className="menu-item-btn logout-btn"
                                component={Link}
                                to="/logout"
                                sx={collapsed ? { justifyContent: 'center', px: 0 } : {}}
                            >
                                <ListItemIcon sx={collapsed ? { minWidth: 0 } : {}}>
                                    <LogoutIcon />
                                </ListItemIcon>
                                {!collapsed && <ListItemText primary="Cerrar Sesión" />}
                            </ListItemButton>
                        </Tooltip>
                    </ListItem>

                </List>

                {/* Boton colapsar/expandir – solo desktop */}
                {isDesktop && (
                    <Box sx={{ display: 'flex', justifyContent: collapsed ? 'center' : 'flex-end', px: 1, pt: 0.5 }}>
                        <Tooltip title={collapsed ? 'Expandir menú' : 'Colapsar menú'} placement="right">
                            <IconButton
                                size="small"
                                onClick={() => setDesktopCollapsed(v => !v)}
                                className="sidebar-collapse-btn"
                            >
                                {collapsed ? <ChevronRightIcon fontSize="small" /> : <ChevronLeftIcon fontSize="small" />}
                            </IconButton>
                        </Tooltip>
                    </Box>
                )}
            </Box>
        </Box>
    );

    return (
        <Box className="layout-root">

            {/* ── AppBar superior – solo en movil ── */}
            {isMobile && (
                <AppBar position="fixed" elevation={0} className="mobile-appbar">
                    <Toolbar variant="dense" sx={{ minHeight: 52 }}>
                        <IconButton
                            edge="start"
                            onClick={() => setMobileOpen(v => !v)}
                            aria-label="Abrir menú"
                            sx={{ mr: 1.5, color: 'var(--text-primary)' }}
                        >
                            <MenuIcon />
                        </IconButton>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'var(--text-primary)', flexGrow: 1, fontSize: '1rem' }}>
                            Monitorización
                        </Typography>
                        <Tooltip title={isDark ? 'Modo Claro' : 'Modo Oscuro'}>
                            <IconButton
                                size="small"
                                onClick={toggleTheme}
                                sx={{ color: '#f59e0b' }}
                            >
                                {isDark ? <LightModeIcon /> : <DarkModeIcon />}
                            </IconButton>
                        </Tooltip>
                    </Toolbar>
                </AppBar>
            )}

            {/* ── Drawer temporal (movil) ── */}
            {isMobile && (
                <Drawer
                    className="layout-drawer"
                    variant="temporary"
                    open={mobileOpen}
                    onClose={() => setMobileOpen(false)}
                    ModalProps={{ keepMounted: true }}
                    sx={{
                        [`& .MuiDrawer-paper`]: {
                            width: DRAWER_FULL,
                            boxSizing: 'border-box',
                            border: 'none',
                        },
                    }}
                >
                    {/* Cabecera del drawer con boton de cerrar */}
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2, py: 1.5, borderBottom: '1px solid var(--border-color)' }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'var(--text-primary)', fontSize: '1rem' }}>
                            Monitorización
                        </Typography>
                        <IconButton size="small" onClick={() => setMobileOpen(false)} sx={{ color: 'var(--text-secondary)' }}>
                            <ChevronLeftIcon />
                        </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100% - 57px)' }}>
                        <Box sx={{ overflow: 'auto', flexGrow: 1, pt: 1 }}>
                            <List>
                                {menuOptions.map((item, index) => (
                                    <ProtecterMenuItem
                                        key={index}
                                        item={item}
                                        collapsed={false}
                                        onNavigate={() => setMobileOpen(false)}
                                    />
                                ))}
                            </List>
                        </Box>
                        <Divider sx={{ borderColor: 'var(--border-color)' }} />
                        <List disablePadding sx={{ py: 1 }}>
                            <ListItem disablePadding>
                                <ListItemButton
                                    className="menu-item-btn"
                                    component={Link}
                                    to="/profile"
                                    selected={location.pathname === '/profile'}
                                    onClick={() => setMobileOpen(false)}
                                >
                                    <ListItemIcon><ProfileIcon /></ListItemIcon>
                                    <ListItemText primary="Perfil" />
                                </ListItemButton>
                            </ListItem>
                            <ListItem disablePadding>
                                <ListItemButton
                                    className="menu-item-btn logout-btn"
                                    component={Link}
                                    to="/logout"
                                >
                                    <ListItemIcon><LogoutIcon /></ListItemIcon>
                                    <ListItemText primary="Cerrar Sesión" />
                                </ListItemButton>
                            </ListItem>
                        </List>
                    </Box>
                </Drawer>
            )}

            {/* ── Drawer permanente (tablet / desktop) ── */}
            {!isMobile && (
                <Drawer
                    className="layout-drawer"
                    variant="permanent"
                    sx={{
                        width: drawerWidth,
                        flexShrink: 0,
                        transition: 'width 0.25s ease',
                        [`& .MuiDrawer-paper`]: {
                            width: drawerWidth,
                            boxSizing: 'border-box',
                            border: 'none',
                            overflowX: 'hidden',
                            transition: 'width 0.25s ease',
                        },
                    }}
                >
                    {drawerContent(isCollapsed)}
                </Drawer>
            )}

            {/* ── Contenido principal ── */}
            <Box
                component="main"
                className="layout-content"
                sx={isMobile ? { mt: '52px', height: 'calc(100vh - 52px)' } : {}}
            >
                <Outlet />
            </Box>

        </Box>
    );
}

export default MainLayout;