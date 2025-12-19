import React, { useEffect, useState } from 'react';
import {
    Box, Typography, Paper, Chip, Dialog, DialogTitle,
    DialogContent, DialogActions, Button, TextField, IconButton
} from '@mui/material';

import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';

import api from '../api';
import PermissionsMenu from './PermissionsMenu'; 

const API_PATH_USER_GROUPS = "/users-groups/";

function UserGroup({ group, allPermissions, onGroupUpdated, onGroupDelete, setNotification }) {

    const PERMISSIONS = allPermissions;
    const [open, setOpen] = useState(false);
    const [localGroup, setLocalGroup] = useState({
        id: group.id,
        name: group.name,
        permissions: group.permissions
    });

    const [anchorEl, setAnchorEl] = useState(null);
    const [avaliablePermissions, setAvaliablePermissions] = useState([]);
    const [newName, setNewName] = useState(group.name);
    const [permissions, setPermisions] = useState([]);

    const handleOpenMenu = (event) => setAnchorEl(event.currentTarget);
    const handleCloseMenu = () => setAnchorEl(null);

    useEffect(() => {
        setLocalGroup({
            id: group.id,
            name: group.name,
            permissions: group.permissions
        });
        setPermisions([...group.permissions]);
        setNewName(group.name); 
    }, [group]);

    const handleOpenGroup = () => {
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    const handleSaveChanges = () => {
        const newGroup = {
            id: group.id,
            name: newName,
            permissions: [...permissions.map((p) => p.id)]
        };

        const updateGroup = async () => {
            try {
                const { status } = await api.patch(API_PATH_USER_GROUPS + `${newGroup.id}/`, newGroup);
                
                if (status < 300) {
                    setNotification({ open: true, message: 'Grupo actualizado correctamente', severity: 'success' });
                    onGroupUpdated({
                        ...newGroup,
                        permissions: permissions 
                    });
                    setOpen(false);
                } else {
                    throw new Error();
                }
            } catch (err) {
                console.log(err);
                setNotification({ open: true, message: 'No se ha podido actualizado el grupo', severity: 'error' });
            }
        };

        updateGroup();
        handleClose();
    };

    const handleDeleteGroup = () => {
        const deleteGroup = async () => {
            try {
                const idGrupo = localGroup.id;
                const { status } = await api.delete(API_PATH_USER_GROUPS + `${localGroup.id}/`);

                if (status < 300) {
                    setNotification({ open: true, message: 'Grupo eliminado correctamente', severity: 'success' });
                    onGroupDelete(idGrupo);
                } else {
                    throw new Error();
                }
            } catch (err) {
                console.log(err);
                setNotification({ open: true, message: 'No se pudo eliminar el grupo', severity: 'error' });
            }
        };

        deleteGroup();
        handleClose();
    };


    // --- GESTIÓN DE PERMISOS ---

    const handleAddPermission = (perm) => {
        setPermisions([
            ...permissions,
            perm
        ]);
    };

    const handleDeletePermission = (permId) => {
        setPermisions(permissions.filter((permission) => permission.id !== permId));
    };

    // Recalcular permisos disponibles (Available = All - Current)
    useEffect(() => {
        const currentIds = permissions.map(p => p.id);
        setAvaliablePermissions(
            PERMISSIONS.filter((p) => !currentIds.includes(p.id))
        );
    }, [permissions, PERMISSIONS]);

    return (
        <div>
            <Paper
                key={localGroup.id}
                className="group-row"
                elevation={0}
                onClick={() => handleOpenGroup()}
            >
                {/* 1. NOMBRE DEL GRUPO */}
                <Typography variant="body1" sx={{ fontWeight: 'bold', minWidth: '150px', color: '#fff' }}>
                    {localGroup.name}
                </Typography>

                {/* 2. PERMISOS (Chips visuales en la lista) */}
                <div className="permissions-container">
                    {localGroup.permissions.map((perm) => (
                        <Chip
                            key={perm.id}
                            label={perm.name}
                            className="permission-chip"
                            size="small"
                        />
                    ))}
                </div>

                {/* 3. ICONO EDITAR */}
                <EditIcon sx={{ color: '#555', fontSize: '1.1rem', minWidth: '24px' }} />
            </Paper>

            {/* --- MODAL DE EDICIÓN --- */}
            <Dialog open={open} onClose={handleClose} classes={{ paper: 'group-dialog-paper' }}>
                <DialogTitle sx={{ borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    Editar {localGroup.name}
                    <IconButton onClick={handleClose} sx={{ color: '#aaa' }}><CloseIcon /></IconButton>
                </DialogTitle>
                <DialogContent sx={{ pt: 3 }}>
                    <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 3 }}>
                        
                        {/* INPUT NOMBRE */}
                        <TextField
                            label="Nombre" fullWidth value={newName} onChange={(e) => setNewName(e.target.value)}
                            sx={{
                                '& .MuiInputBase-root': { color: '#fff' },
                                '& .MuiInputLabel-root': { color: '#aaa' },
                                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#555' },
                                '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#8b5cf6' },
                            }}
                        />

                        {/* LISTA DE PERMISOS DENTRO DEL MODAL */}
                        <Box>
                            <Typography variant="caption" sx={{ color: '#8b5cf6', mb: 1, display: 'block' }}>PERMISOS</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                {permissions.map((perm) => (
                                    <Chip
                                        key={perm.id}
                                        label={perm.name}
                                        className="permission-chip"
                                        size="small"
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
                                
                                {/* BOTÓN AÑADIR (+): ABRE EL NUEVO MENÚ */}
                                <IconButton
                                    onClick={handleOpenMenu}
                                    size="small"
                                    sx={{
                                        bgcolor: '#2b2d31', color: '#8b5cf6', border: '1px dashed #555', width: 32, height: 32,
                                        '&:hover': { bgcolor: '#8b5cf6', color: '#fff', borderColor: '#8b5cf6' }
                                    }}
                                >
                                    <AddIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        </Box>
                    </Box>
                </DialogContent>
                
                <DialogActions sx={{ p: 3, borderTop: '1px solid #333', justifyContent: 'space-between' }}>
                    <Button startIcon={<DeleteIcon />} color="error" onClick={handleDeleteGroup}>Eliminar</Button>
                    <Button variant="contained" onClick={handleSaveChanges} sx={{ bgcolor: '#8b5cf6', '&:hover': { bgcolor: '#7c3aed' } }}>Guardar</Button>
                </DialogActions>

                <PermissionsMenu 
                    anchorEl={anchorEl}
                    onClose={handleCloseMenu}
                    permissions={avaliablePermissions} 
                    onAddPermission={handleAddPermission}
                />

            </Dialog>
        </div>
    );
}

export default UserGroup;