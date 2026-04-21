// Pagina de gestion de grupos de usuarios con paginacion y CRUD
// Permite crear editar y eliminar grupos y asignar permisos a cada grupo
import React, { useEffect, useState } from 'react'; 
import {
    Box, Typography, CircularProgress, Snackbar, Alert, Button, Dialog, 
    DialogTitle, IconButton, DialogContent, DialogActions, TextField, Chip,
    Pagination
} from '@mui/material';

import GroupIcon from '@mui/icons-material/Group';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';

import UserGroup from "../components/UserGroup";
import RestrictedAccess from '../components/RestrictedAccess';
import PermissionsMenu from '../components/PermissionsMenu'; 

import { USER_PERMISSIONS , API_PATH_USER_GROUPS, API_PATH_PERMISIONS } from '../constants';
import api from '../api';
import '../styles/UserGroups.css';

const PAGE_SIZE = 10;

const UserGroups = () => {
    const storedUser = localStorage.getItem(USER_PERMISSIONS);
    const user = storedUser ? JSON.parse(storedUser) : { permissions: [], is_superuser: false };

    const [loading, setloading] = useState(false);
    const [groups, setGroups] = useState([]);
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    
    // Estados de paginacion
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [allPermissions, setAllPermissions] = useState([]);
    const [avaliablePermissions, setAvaliablePermissions] = useState([]);
    
    // Estado del modal de creacion de grupo
    const [open, setOpen] = useState(false);
    const [newName, setNewName] = useState("");
    const [newGroupPermisions, setNewGroupPermisions] = useState([]);
    
    // Estado del menu desplegable de permisos
    const [anchorEl, setAnchorEl] = useState(null);

    const fetchUserGroups = async (pageNumber = page) => {
        try {
            setloading(true);
            const { data, status } = await api.get(API_PATH_USER_GROUPS, {
                params: { page: pageNumber }
            });

            if (status === 200) {

                setGroups(data.results);
                
                const total = data.count;
                setTotalPages(Math.ceil(total / PAGE_SIZE));
            }
        } catch (err) {
            console.error(err);
            setNotification({ open: true, message: 'Error al cargar los grupos', severity: 'error' });
        } finally {
            setloading(false);
        }
    };

    useEffect(() => {
        const fetchPermissions = async () => {
            try {
                const { data, status } = await api.get(API_PATH_PERMISIONS);
                if (status === 200) {
                    setAllPermissions([...data]);
                    setAvaliablePermissions([...data]);
                }
            } catch {
                setNotification({ open: true, message: 'Error al cargar los permisos', severity: 'warning' });
            }
        };

        fetchPermissions();
    }, []);

    useEffect(() => {
        fetchUserGroups(page);
    }, [page, fetchUserGroups]); 

    const handlePageChange = (event, value) => {
        setPage(value);
    };

    const handleOpenMenu = (event) => setAnchorEl(event.currentTarget);
    const handleCloseMenu = () => setAnchorEl(null);

    const handleAddPermission = (perm) => {
        setNewGroupPermisions([...newGroupPermisions, perm]);
    };

    const handleDeletePermission = (permId) => {
        setNewGroupPermisions(newGroupPermisions.filter((p) => p.id !== permId));
    };

    useEffect(() => {
        const currentIds = newGroupPermisions.map(p => p.id);
        const available = allPermissions.filter(p => !currentIds.includes(p.id));
        setAvaliablePermissions(available);
    }, [newGroupPermisions, allPermissions]);


    const handleGroupUpdated = (updatedGroup) => {
        const newList = groups.map(g => g.id === updatedGroup.id ? updatedGroup : g);
        setGroups(newList);
    };

    const handleGroupDeleted = () => {
        fetchUserGroups(page); 
    };

    const handleOpenGroup = () => setOpen(true);

    const handleClose = () => {
        setOpen(false);
        setNewName("");
        setNewGroupPermisions([]);
    };

    const handleSaveChanges = async () => {
        const newGroup = {
            name: newName,
            permissions: newGroupPermisions.map((p) => p.id)
        };

        try {
            const { status } = await api.post(API_PATH_USER_GROUPS, newGroup);
            if (status < 300) {
                setNotification({ open: true, message: 'Grupo creado correctamente', severity: 'success' });
                fetchUserGroups(page);
                handleClose();
            } else {
                throw new Error();
            }
        } catch {
            setNotification({ open: true, message: 'No se ha podido crear el grupo', severity: 'error' });
        }
    };

    return (
        <div className="groups-container">
            
            {loading && groups.length === 0 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <CircularProgress sx={{ color: 'var(--accent-color)' }} />
                </Box>
            )}

            {!loading && !user.is_superuser && !user.permissions.includes("auth.view_group") && (
                <RestrictedAccess />
            )}

            {(user.is_superuser || user.permissions.includes("auth.view_group")) && (
                <>
                    <Box className="groups-header">
                        <Typography variant="h5" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                            <GroupIcon sx={{ color: 'var(--accent-color)' }} />
                            Grupos
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleOpenGroup}
                            sx={{
                                backgroundColor: 'var(--accent-color)',
                                color: 'var(--text-on-accent)',
                                fontWeight: 'bold',
                                textTransform: 'none',
                                borderRadius: '10px',
                                padding: '5px 14px',
                            }}
                        >
                            Crear Grupo
                        </Button>
                    </Box>

                    <div className="groups-list">
                        {loading && groups.length > 0 && <CircularProgress sx={{ color: 'var(--accent-color)' }} />}
                        
                        {groups.map((group, idx) => (
                            <UserGroup 
                                key={group.id || idx} 
                                group={group} 
                                allPermissions={allPermissions} 
                                onGroupUpdated={handleGroupUpdated} 
                                onGroupDelete={handleGroupDeleted} 
                                setNotification={setNotification} 
                            />
                        ))}
                    </div>

                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3, pb: 2 }}>
                        <Pagination 
                            count={totalPages} 
                            page={page} 
                            onChange={handlePageChange}
                            variant="outlined"
                            shape="rounded"
                            sx={{
                                '& .MuiPaginationItem-root': { color: 'var(--text-primary)', borderColor: 'var(--border-lighter)' },
                                '& .Mui-selected': { 
                                    backgroundColor: 'var(--accent-color) !important', 
                                    borderColor: 'var(--accent-color)',
                                    fontWeight: 'bold' 
                                },
                                '& .MuiPaginationItem-root:hover': { backgroundColor: 'var(--accent-bg)' }
                            }}
                        />
                    </Box>

                    {/* Dialogo para crear un nuevo grupo */}
                    <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                        <DialogTitle sx={{ borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            Crear Grupo
                            <IconButton onClick={handleClose} sx={{ color: 'var(--text-secondary)' }}><CloseIcon /></IconButton>
                        </DialogTitle>
                        <DialogContent sx={{ pt: 3 }}>
                            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                                <TextField
                                    label="Nombre del Grupo"
                                    fullWidth
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    sx={{
                                        '& .MuiInputBase-root': { color: 'var(--text-primary)' },
                                        '& .MuiInputLabel-root': { color: 'var(--text-secondary)' },
                                        '& .MuiOutlinedInput-notchedOutline': { borderColor: 'var(--border-lighter)' },
                                        '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: 'var(--accent-color)' },
                                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: 'var(--accent-color)' },
                                    }}
                                />
                                <Box>
                                    <Typography variant="caption" sx={{ color: 'var(--accent-color)', mb: 1, display: 'block' }}>PERMISOS</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {newGroupPermisions.map((perm) => (
                                            <Chip
                                                key={perm.id}
                                                label={perm.name}
                                                onDelete={() => handleDeletePermission(perm.id)}
                                                sx={{
                                                    backgroundColor: 'var(--accent-bg)',
                                                    color: 'var(--accent-medium)',
                                                    border: '1px solid var(--accent-border-strong)',
                                                    '& .MuiChip-deleteIcon': {
                                                        color: 'var(--accent-medium)',
                                                        '&:hover': { color: 'var(--danger-color)' }
                                                    }
                                                }}
                                            />
                                        ))}
                                        <IconButton
                                            onClick={handleOpenMenu}
                                            size="small"
                                            sx={{
                                                bgcolor: 'var(--bg-input)',
                                                color: 'var(--accent-color)',
                                                border: '1px dashed var(--border-lighter)',
                                                width: 32, height: 32,
                                                '&:hover': { bgcolor: 'var(--accent-color)', color: 'var(--text-on-accent)', borderColor: 'var(--accent-color)' }
                                            }}
                                        >
                                            <AddIcon fontSize="small" />
                                        </IconButton>
                                    </Box>
                                </Box>
                            </Box>
                        </DialogContent>
                        <DialogActions sx={{ p: 3, borderTop: '1px solid var(--border-color)' }}>
                            <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: 'var(--accent-color)', '&:hover': { bgcolor: 'var(--accent-hover)' } }}>Crear Grupo</Button>
                        </DialogActions>

                        <PermissionsMenu 
                            anchorEl={anchorEl}
                            onClose={handleCloseMenu}
                            permissions={avaliablePermissions}
                            onAddPermission={handleAddPermission}
                        />

                    </Dialog>
                </>
            )}

            <Snackbar
                open={notification.open}
                autoHideDuration={4000}
                onClose={() => setNotification({ ...notification, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert severity={notification.severity} variant="filled" sx={{ width: '100%' }}>
                    {notification.message}
                </Alert>
            </Snackbar>
        </div>
    );
};

export default UserGroups;