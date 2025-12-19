import React, { useEffect, useState } from 'react'; 
import {
    Box, Typography, CircularProgress, Snackbar, Alert, Button, Dialog, 
    DialogTitle, IconButton, DialogContent, DialogActions, TextField, Chip,
    Pagination // <--- 1. IMPORTADO PAGINATION
} from '@mui/material';

import GroupIcon from '@mui/icons-material/Group';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';

import UserGroup from "../components/UserGroup";
import RestrictedAccess from '../components/RestrictedAccess';
import PermissionsMenu from '../components/PermissionsMenu'; 

import { USER_PERMISSIONS } from '../constants';
import api from '../api';
import '../styles/UserGroups.css';

const API_PATH_USER_GROUPS = "/users-groups/";
const API_PATH_PERMISIONS = "/permissions/";
const PAGE_SIZE = 10;

const UserGroups = () => {
    const storedUser = localStorage.getItem(USER_PERMISSIONS);
    const user = storedUser ? JSON.parse(storedUser) : { permissions: [], is_superuser: false };

    const [loading, setloading] = useState(false);
    const [groups, setGroups] = useState([]);
    const [notification, setNotification] = useState({ open: false, message: '', severity: 'success' });
    
    //ESTADOS PARA PAGINACION
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [allPermissions, setAllPermissions] = useState([]);
    const [avaliablePermissions, setAvaliablePermissions] = useState([]);
    
    // Modal Crear Grupo
    const [open, setOpen] = useState(false);
    const [newName, setNewName] = useState("");
    const [newGroupPermisions, setNewGroupPermisions] = useState([]);
    
    // Menu desplegable
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
            } catch (err) {
                setNotification({ open: true, message: 'Error al cargar los permisos', severity: 'warning' });
            }
        };

        fetchPermissions();
    }, []);

    useEffect(() => {
        fetchUserGroups(page);
    }, [page]); 

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

    const handleGroupDeleted = (idDeleted) => {
        //setGroups(prevGroups => prevGroups.filter(g => g.id !== idDeleted));
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
        } catch (err) {
            setNotification({ open: true, message: 'No se ha podido crear el grupo', severity: 'error' });
        }
    };

    return (
        <div className="groups-container">
            
            {loading && groups.length === 0 && (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <CircularProgress sx={{ color: '#8b5cf6' }} />
                </Box>
            )}

            {!loading && !user.is_superuser && !user.permissions.includes("auth.view_group") && (
                <RestrictedAccess />
            )}

            {(user.is_superuser || user.permissions.includes("auth.view_group")) && (
                <>
                    <Box className="groups-header">
                        <Typography variant="h5" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                            <GroupIcon sx={{ color: '#8b5cf6' }} />
                            Grupos
                        </Typography>
                        <Button
                            variant="contained"
                            startIcon={<AddIcon />}
                            onClick={handleOpenGroup}
                            sx={{
                                backgroundColor: '#8b5cf6',
                                color: '#fff',
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
                        {loading && groups.length > 0 && <CircularProgress sx={{ color: '#8b5cf6' }} />}
                        
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
                                '& .MuiPaginationItem-root': { color: '#fff', borderColor: '#555' },
                                '& .Mui-selected': { 
                                    backgroundColor: '#8b5cf6 !important', 
                                    borderColor: '#8b5cf6',
                                    fontWeight: 'bold' 
                                },
                                '& .MuiPaginationItem-root:hover': { backgroundColor: 'rgba(139, 92, 246, 0.2)' }
                            }}
                        />
                    </Box>

                    {/*DIALOG CREAR GRUPO*/}
                    <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                        <DialogTitle sx={{ borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            Crear Grupo
                            <IconButton onClick={handleClose} sx={{ color: '#aaa' }}><CloseIcon /></IconButton>
                        </DialogTitle>
                        <DialogContent sx={{ pt: 3 }}>
                            <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                                <TextField
                                    label="Nombre del Grupo"
                                    fullWidth
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    sx={{
                                        '& .MuiInputBase-root': { color: '#fff' },
                                        '& .MuiInputLabel-root': { color: '#aaa' },
                                        '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' },
                                        '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                                    }}
                                />
                                <Box>
                                    <Typography variant="caption" sx={{ color: '#8b5cf6', mb: 1, display: 'block' }}>PERMISOS</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {newGroupPermisions.map((perm) => (
                                            <Chip
                                                key={perm.id}
                                                label={perm.name}
                                                onDelete={() => handleDeletePermission(perm.id)}
                                                sx={{
                                                    backgroundColor: 'rgba(139, 92, 246, 0.15)',
                                                    color: '#a78bfa',
                                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                                    '& .MuiChip-deleteIcon': {
                                                        color: '#a78bfa',
                                                        '&:hover': { color: '#ff4d4d' }
                                                    }
                                                }}
                                            />
                                        ))}
                                        <IconButton
                                            onClick={handleOpenMenu}
                                            size="small"
                                            sx={{
                                                bgcolor: '#2b2d31',
                                                color: '#8b5cf6',
                                                border: '1px dashed #555',
                                                width: 32, height: 32,
                                                '&:hover': { bgcolor: '#8b5cf6', color: '#fff', borderColor: '#8b5cf6' }
                                            }}
                                        >
                                            <AddIcon fontSize="small" />
                                        </IconButton>
                                    </Box>
                                </Box>
                            </Box>
                        </DialogContent>
                        <DialogActions sx={{ p: 3, borderTop: '1px solid #333' }}>
                            <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: '#8b5cf6', '&:hover': { bgcolor: '#7c3aed' } }}>Crear Grupo</Button>
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